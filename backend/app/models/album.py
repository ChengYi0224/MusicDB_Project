from app.extensions import db
from sqlalchemy.ext.associationproxy import association_proxy

# 中介模型 (Junction/Association Model)
class AlbumSong(db.Model):
    __tablename__ = 'album_songs'
    album_id = db.Column(db.Integer, db.ForeignKey('albums.album_id'), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), primary_key=True)
    track_num = db.Column(db.Integer, nullable=False, comment='專輯中的曲目編號')

    # 反向關係，指向 Album 和 Song 模型
    album = db.relationship('Album', back_populates='song_entries')
    song = db.relationship('Song', back_populates='album_entries')

# 主要模型
class Album(db.Model):
    __tablename__ = 'albums'

    album_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    cover_url = db.Column(db.Text, nullable=False)
    release_date = db.Column(db.DateTime, nullable=False)

    # 與 User 的關係
    user = db.relationship('User', back_populates='albums')

    # 1. 與中介模型 AlbumSong 的直接關係
    song_entries = db.relationship(
        'AlbumSong',
        back_populates='album',
        cascade="all, delete-orphan",
        order_by='AlbumSong.track_num' # 建議加上排序
    )

    # 2. 透過 association_proxy 建立方便的 'songs' 列表
    songs = association_proxy('song_entries', 'song')