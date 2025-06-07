# models/playlist.py
from app.extensions import db
from sqlalchemy.ext.associationproxy import association_proxy

class Playlist(db.Model):
    __tablename__ = 'playlists'

    playlist_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='歌單ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='建立者ID')
    title = db.Column(db.String(255), nullable=False, comment='歌單名稱')
    is_public = db.Column(db.Boolean, nullable=False, default=True)

    # 與建立者 User 的關係
    user = db.relationship('User', back_populates='playlists')

    # 1. 【建議更名並優化】與中介模型 PlaylistSong 的直接關係
    #    將 'playlist_songs' 更名為 'song_entries' 以保持命名一致性
    #    並建議加上排序，確保每次取出的歌曲順序都正確
    song_entries = db.relationship(
        'PlaylistSong', 
        back_populates='playlist',
        cascade="all, delete-orphan",
        order_by='PlaylistSong.track_num' # 依照曲目編號排序
    )
    
    # 2. 【新增】方便存取歌曲列表的 association_proxy
    #    讓你可以直接用 my_playlist.songs 來取得 [Song, Song, ...]
    songs = association_proxy('song_entries', 'song')