from sqlalchemy import case, func
# 如果輔助函數需要直接使用模型，可以在這裡導入，或者將模型作為參數傳入
# from ..models import Song, User # 假設的導入路徑
from sqlalchemy.orm import joinedload

def _calculate_song_relevance_score(SongModel, query_string, search_term_exact, search_term_starts_with, search_term_contains):
    """計算歌曲標題的相關性分數 (輔助內部使用或獨立使用)"""
    return case(
        (SongModel.title.ilike(search_term_exact), 3),
        (SongModel.title.ilike(search_term_starts_with), 2),
        (SongModel.title.ilike(search_term_contains), 1),
        else_=0
    ).label("relevance_score")

def _calculate_playlist_relevance_score(PlaylistModel, query_string, search_term_exact, search_term_starts_with, search_term_contains):
    """計算播放清單標題的相關性分數"""
    return case(
        (PlaylistModel.title.ilike(search_term_exact), 3),
        (PlaylistModel.title.ilike(search_term_starts_with), 2),
        (PlaylistModel.title.ilike(search_term_contains), 1),
        else_=0
    ).label("relevance_score")

def find_songs_by_title(db_session, SongModel, UserModel, query_string):
    """
    根據標題搜尋歌曲，並按相關性排序。
    返回格式化後的歌曲結果列表。
    """
    if not query_string:
        return []

    search_term_exact = query_string
    search_term_starts_with = f"{query_string}%"
    search_term_contains = f"%{query_string}%"

    relevance_expr = _calculate_song_relevance_score(
        SongModel, query_string, search_term_exact, 
        search_term_starts_with, search_term_contains
    )

    ordered_songs = db_session.query(SongModel)\
        .join(UserModel, SongModel.user_id == UserModel.user_id)\
        .options(joinedload(SongModel.user))\
        .filter(SongModel.is_public == True)\
        .filter(SongModel.title.ilike(search_term_contains))\
        .order_by(relevance_expr.desc(), SongModel.title.asc())\
        .all()

    results = []
    for song in ordered_songs:
        results.append({
            'type': '歌曲',
            'id': song.song_id,
            'title': song.title,
            'artist_name': song.user.username if song.user else "未知歌手",
            'file_url': song.file_url
        })
    return results

def find_playlists_by_title(db_session, PlaylistModel, UserModel, query_string):
    """
    根據標題搜尋公開的播放清單，並按相關性排序。
    返回格式化後的播放清單結果列表。
    """
    if not query_string:
        return []

    search_term_exact = query_string
    search_term_starts_with = f"{query_string}%"
    search_term_contains = f"%{query_string}%"

    relevance_expr = _calculate_playlist_relevance_score(
        PlaylistModel, query_string, search_term_exact, 
        search_term_starts_with, search_term_contains
    )

    ordered_playlists = db_session.query(PlaylistModel)\
        .join(UserModel, PlaylistModel.user_id == UserModel.user_id)\
        .options(joinedload(PlaylistModel.user))\
        .filter(PlaylistModel.is_public == True)\
        .filter(PlaylistModel.title.ilike(search_term_contains))\
        .order_by(relevance_expr.desc(), PlaylistModel.title.asc())\
        .all()

    results = []
    for playlist in ordered_playlists:
        results.append({
            'type': '播放清單',
            'id': playlist.playlist_id,
            'title': playlist.title,
            # 使用 playlist.user 來取得建立者名稱
            'artist_name': playlist.user.username if playlist.user else "未知創作者",
            # 提供一個點擊後可以前往的 URL
            'url': f"/playlists/{playlist.playlist_id}" 
        })
    return results