#app/routes/default.py
from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from app.extensions import db
from app.models import Song, User, Playlist # 導入模型
from app.utils.search_helpers import find_songs_by_title, find_playlists_by_title, get_homepage_playlists

default_bp = Blueprint('default', __name__, url_prefix='/')

@default_bp.route('/', methods=['GET'])
def index():
    query_string = request.args.get('q', '').strip()
    search_results = []
    

    if query_string:
        # 使用輔助函數搜尋歌曲
        song_results = find_songs_by_title(db.session, Song, User, query_string)
        search_results.extend(song_results)

        playlist_results = find_playlists_by_title(db.session, Playlist, User, query_string)
        search_results.extend(playlist_results)

        if not search_results: # 檢查最終的 search_results
            search_results.append({'type': '提示', 'message': f"找不到與 '{query_string}' 相關的內容。"})

    # 查詢所有公開的歌曲和播放清單
    # .limit(20) 可以避免一次載入過多資料，可以依需求調整
    all_songs = Song.query.filter_by(is_public=True).limit(20).all()

    user_id = session.get('user_id')
    all_playlists = get_homepage_playlists(db.session, Playlist, user_id=user_id, limit=20)
        
    return render_template('index.html', 
                           query=query_string, 
                           results=search_results, 
                           # user=logged_in_user,   # 由 context processor 處理
                           songs=all_songs,         # 傳遞歌曲資料到前端
                           playlists=all_playlists  # 傳遞播放清單資料到前端
                           )