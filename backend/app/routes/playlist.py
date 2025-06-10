# app/routes/playlist.py

from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from sqlalchemy import func
from app.models import Playlist, PlaylistSong, Song
from app.extensions import db
from sqlalchemy.orm import selectinload
import sys

# 建立一個新的 Blueprint
playlist_bp = Blueprint('playlist', __name__, url_prefix='/playlists')

@playlist_bp.route('/<int:playlist_id>')
def view_playlist(playlist_id):
    """
    顯示單一播放清單的詳細頁面
    """
    # 【修改】使用 options 來預先載入並排序關聯的歌曲
    # 這樣可以確保 playlist.song_entries 永遠是依 track_num 排序的
    playlist = Playlist.query.options(
        selectinload(Playlist.song_entries).joinedload(PlaylistSong.song).joinedload(Song.user)
    ).get_or_404(playlist_id)

    # 雖然模型已定義排序，但在 route 中明確指定是更保險的做法
    # 確保 song_entries 是排序過的
    playlist.song_entries.sort(key=lambda x: x.track_num)
    
    return render_template('playlist_detail.html', playlist=playlist)

@playlist_bp.route('/api/my-playlists', methods=['GET'])
def get_my_playlists():
    """API: 獲取當前登入使用者的所有播放清單。"""
    if 'user_id' not in session:
        return jsonify({'error': '使用者未登入'}), 401

    user_id = session['user_id']
    playlists = Playlist.query.filter_by(user_id=user_id).order_by(Playlist.title).all()
    
    # 將結果序列化為 JSON 陣列
    playlists_data = [{'id': p.playlist_id, 'title': p.title} for p in playlists]
    return jsonify(playlists_data)


@playlist_bp.route('/api/add-song', methods=['POST'])
def add_song_to_playlist_api():
    """API: 將歌曲新增到現有或新的播放清單。"""
    if 'user_id' not in session:
        return jsonify({'error': '需要登入才能執行此操作'}), 401

    user_id = session['user_id']
    data = request.get_json()
    song_id = data.get('song_id')
    playlist_id = data.get('playlist_id')
    new_playlist_title = data.get('new_playlist_title')

    if not song_id:
        return jsonify({'error': '缺少歌曲 ID'}), 400

    target_playlist = None
    # --- 情況1：新增到新的播放清單 ---
    if new_playlist_title:
        # 建立新的 Playlist 物件
        new_playlist = Playlist(
            user_id=user_id,
            title=new_playlist_title.strip(),
            is_public=False # 預設為公開，可依需求調整
        )
        db.session.add(new_playlist)
        db.session.flush() # flush 以便獲取 new_playlist.playlist_id
        target_playlist = new_playlist
    # --- 情況2：新增到現有的播放清單 ---
    elif playlist_id:
        target_playlist = Playlist.query.get(playlist_id)
        # 驗證這個歌單是否屬於當前使用者
        if not target_playlist or target_playlist.user_id != user_id:
            return jsonify({'error': '無效的播放清單或權限不足'}), 403
    else:
        return jsonify({'error': '缺少播放清單 ID 或新播放清單標題'}), 400

    # 檢查歌曲是否已存在於歌單中
    existing_entry = PlaylistSong.query.filter_by(
        playlist_id=target_playlist.playlist_id, 
        song_id=song_id
    ).first()
    if existing_entry:
        return jsonify({'error': f'歌曲已存在於播放清單 "{target_playlist.title}" 中'}), 409

    # 決定 track_num (加到最後)
    # 使用 subquery 來找到該歌單目前最大的 track_num
    max_track_num = db.session.query(func.max(PlaylistSong.track_num))\
        .filter(PlaylistSong.playlist_id == target_playlist.playlist_id)\
        .scalar()
    
    new_track_num = (max_track_num or 0) + 1

    # 建立 PlaylistSong 關聯
    new_entry = PlaylistSong(
        playlist_id=target_playlist.playlist_id,
        song_id=song_id,
        track_num=new_track_num,
        added_by_user_id=user_id
    )
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({
        'success': True, 
        'message': f'成功將歌曲加入 "{target_playlist.title}"',
        'playlist_name': target_playlist.title
    }), 201

@playlist_bp.route('/api/<int:playlist_id>/reorder', methods=['POST'])
def reorder_playlist_songs(playlist_id):
    """API: 更新播放清單中歌曲的順序。"""
    if 'user_id' not in session:
        return jsonify({'error': '需要登入才能執行此操作'}), 401
    
    user_id = session['user_id']
    playlist = Playlist.query.get(playlist_id)

    if not playlist or playlist.user_id != user_id:
        return jsonify({'error': '無效的播放清單或權限不足'}), 403

    data = request.get_json()
    ordered_song_ids = data.get('song_ids')

    if not isinstance(ordered_song_ids, list):
        return jsonify({'error': '無效的資料格式'}), 400

    # 開始一個 transaction 來更新所有 track_num
    try:
        # 一次性載入此播放清單的所有 PlaylistSong 項目
        entries = PlaylistSong.query.filter_by(playlist_id=playlist_id).all()
        entry_map = {str(entry.song_id): entry for entry in entries} # 使用字串 key 來比對
        song_count = len(entries)

        # 【第一階段】將所有 track_num 更新為臨時值，避免唯一性衝突
        # 將每個 track_num 加上歌曲總數，確保它們不會和 1..N 的目標值衝突
        for entry in entries:
            entry.track_num += song_count
        
        # 將第一階段的變更送到資料庫，但先不 commit
        db.session.flush()

        # 【第二階段】設定為最終的正確 track_num
        for index, song_id in enumerate(ordered_song_ids):
            # 從 map 中找到對應的 entry
            entry_to_update = entry_map.get(str(song_id))
            if entry_to_update:
                # 更新 track_num，index 從 0 開始，track_num 我們習慣從 1 開始
                entry_to_update.track_num = index + 1
            else:
                # 記錄一個警告，如果前端傳來的 song_id 不在歌單中
                print(f"警告：在播放清單 {playlist_id} 中找不到 song_id {song_id} 的項目。")
        
        # 提交整個交易
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # 在伺服器後台印出詳細的錯誤訊息
        print(f"更新播放清單順序時發生錯誤: {e}")
        return jsonify({'error': '更新順序時發生資料庫錯誤'}), 500

    return jsonify({'success': True, 'message': '播放清單順序已更新'})

@playlist_bp.route('/api/<int:playlist_id>/set-privacy', methods=['POST'])
def set_playlist_privacy(playlist_id):
    """
    API: 設定播放清單的公開/私密狀態。
    """
    # 步驟 1: 檢查使用者是否登入
    if 'user_id' not in session:
        return jsonify({'error': '需要登入才能執行此操作'}), 401
    
    user_id = session['user_id']
    
    # 步驟 2: 查找播放清單並驗證擁有權
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        return jsonify({'error': '找不到指定的播放清單'}), 404
    
    if playlist.user_id != user_id:
        return jsonify({'error': '您沒有權限修改此播放清單'}), 403

    # 步驟 3: 從前端請求中獲取新的狀態
    data = request.get_json()
    if 'is_public' not in data or not isinstance(data['is_public'], bool):
        return jsonify({'error': '無效的請求資料'}), 400
        
    new_status = data['is_public']

    # 步驟 4: 更新資料庫
    try:
        playlist.is_public = new_status
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"更新播放清單隱私狀態時發生錯誤: {e}")
        return jsonify({'error': '更新時發生伺服器錯誤'}), 500

    # 步驟 5: 回傳成功訊息
    return jsonify({
        'success': True,
        'message': '播放清單狀態已更新',
        'is_public': new_status
    })
