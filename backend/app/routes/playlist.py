# app/routes/playlist.py

from flask import Blueprint, render_template
from app.models import Playlist

# 建立一個新的 Blueprint
playlist_bp = Blueprint('playlist', __name__, url_prefix='/playlists')

@playlist_bp.route('/<int:playlist_id>')
def view_playlist(playlist_id):
    """
    顯示單一播放清單的詳細頁面
    """
    # 根據 ID 從資料庫查詢播放清單，如果找不到會自動回傳 404 Not Found
    playlist = Playlist.query.get_or_404(playlist_id)
    
    # 渲染一個新的樣板，並將查詢到的 playlist 物件傳過去
    # playlist 物件中已經可以透過 playlist.songs 取得所有歌曲
    return render_template('playlist_detail.html', playlist=playlist)