
# from ..models import Song, User # 假設的導入路徑
from sqlalchemy import case, func, or_
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

def get_homepage_playlists(db_session, PlaylistModel, user_id=None, limit=20):
    """
    獲取首頁要顯示的播放清單。
    - 已登入使用者：優先顯示自己的私密/公開歌單，接著是其他人的公開歌單。
    - 未登入訪客：只顯示公開歌單。

    :param db_session: 資料庫 session 物件。
    :param PlaylistModel: Playlist 模型類別。
    :param user_id: 當前登入的使用者 ID，可為 None。
    :param limit: 回傳的數量上限。
    :return: 播放清單物件的列表。
    """
    # 建立一個基礎查詢
    playlists_query = db_session.query(PlaylistModel)

    # 1. 過濾條件：只顯示 (is_public=True) 或 (屬於當前使用者) 的歌單
    if user_id:
        playlists_query = playlists_query.filter(
            or_(PlaylistModel.is_public == True, PlaylistModel.user_id == user_id)
        )
    else:
        # 如果未登入，只顯示公開歌單
        playlists_query = playlists_query.filter(PlaylistModel.is_public == True)

    # 2. 排序條件：優先顯示當前使用者的歌單
    if user_id:
        user_first_sorter = case(
            (PlaylistModel.user_id == user_id, 0),
            else_=1
        ).label("user_sort_priority")
        playlists_query = playlists_query.order_by(user_first_sorter, PlaylistModel.title.asc())
    else:
        # 如果未登入，直接按標題排序
        playlists_query = playlists_query.order_by(PlaylistModel.title.asc())
        
    # 最後執行查詢並限制數量
    return playlists_query.limit(limit).all()