from app.extensions import db

class Song(db.Model):
    __tablename__ = 'songs'

    song_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='歌曲ID')
    title = db.Column(db.String(255), nullable=False, comment='歌曲名稱')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='歌手ID')
    duration = db.Column(db.Integer, nullable=False, comment='長度')
    file_url = db.Column(db.String(255), nullable=False, comment='音樂檔案路徑')
    is_public = db.Column(db.Boolean, nullable=False, comment='是否公開')
    album_id = db.Column(db.Integer, db.ForeignKey('albums.album_id'), nullable=True, comment='專輯ID')

    user = db.relationship('User', back_populates='songs')
    album = db.relationship('Album', back_populates='songs')
    album_songs = db.relationship('AlbumSong', back_populates='song')
    playlist_songs = db.relationship('PlaylistSong', back_populates='song')
    user_history = db.relationship('UserHistory', back_populates='song')
    playback_queue = db.relationship('PlaybackQueue', back_populates='song')
