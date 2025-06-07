from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from app.extensions import db
from app.models import Album, Song, User, Playlist # 導入模型
# 從 utils 導入輔助函數
from app.utils.search_helpers import find_songs_by_title #, find_albums_by_title 等

default_bp = Blueprint('default', __name__, url_prefix='/')

@default_bp.route('/', methods=['GET'])
def index():
    query_string = request.args.get('q', '').strip()
    search_results = []
    

    if query_string:
        # 使用輔助函數搜尋歌曲
        song_results = find_songs_by_title(db.session, Song, User, query_string)
        search_results.extend(song_results)
        
        # 對於專輯、使用者、播放清單，也可以使用類似的輔助函數
        # album_results = find_albums_by_title(db.session, Album, User, query_string)
        # search_results.extend(album_results)
        
        # (以下為簡化，您需要為其他類型也建立或調用輔助函數)
        if not song_results: # 假設目前只實作了歌曲搜尋的輔助函數
             # 搜尋專輯 (Albums)
            albums_search_term = f"%{query_string}%"
            found_albums = Album.query.join(User, Album.user_id == User.user_id)\
                .filter(Album.title.ilike(albums_search_term))\
                .all()
            for album in found_albums:
                search_results.append({
                    'type': '專輯',
                    'id': album.album_id,
                    'title': album.title,
                    'artist_name': album.artist.username if hasattr(album, 'artist') and album.artist else "未知歌手",
                    'cover_url': album.cover_url,
                    'url': f"/albums/{album.album_id}"
                })
            # ... (其他模型的搜尋邏輯) ...


        if not search_results and query_string: # 檢查最終的 search_results
            search_results.append({'type': '提示', 'message': f"找不到與 '{query_string}' 相關的內容。"})

    logged_in_user = None
    if 'user_id' in session:
        logged_in_user = User.query.get(session['user_id'])
    print(f"user_id: {session.get('user_id')}, logged_in_user: {logged_in_user}")

    # 查詢所有公開的歌曲和播放清單
    # .limit(20) 可以避免一次載入過多資料，可以依需求調整
    all_songs = Song.query.filter_by(is_public=True).limit(20).all()
    all_playlists = Playlist.query.filter_by(is_public=True).limit(20).all()
            
    return render_template('index.html', 
                           query=query_string, 
                           results=search_results, 
                           user=logged_in_user,
                           songs=all_songs,         # 傳遞歌曲資料到前端
                           playlists=all_playlists  # 傳遞播放清單資料到前端
                           )