from sqlalchemy import case, func
# 如果輔助函數需要直接使用模型，可以在這裡導入，或者將模型作為參數傳入
# from ..models import Song, User # 假設的導入路徑

def _calculate_song_relevance_score(SongModel, query_string, search_term_exact, search_term_starts_with, search_term_contains):
    """計算歌曲標題的相關性分數 (輔助內部使用或獨立使用)"""
    return case(
        (SongModel.title.ilike(search_term_exact), 3),
        (SongModel.title.ilike(search_term_starts_with), 2),
        (SongModel.title.ilike(search_term_contains), 1),
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
            'artist_name': song.artist.username if hasattr(song, 'artist') and song.artist else "未知歌手",
            'url': f"/songs/{song.song_id}"
        })
    return results

# 您可以為 albums, users, playlists 也定義類似的輔助查詢函數
# def find_albums_by_title(db_session, AlbumModel, UserModel, query_string): ...