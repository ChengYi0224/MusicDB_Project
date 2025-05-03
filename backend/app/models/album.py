from app.extensions import db

class Album(db.Model):
    __tablename__ = 'albums'

    album_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='專輯ID')
    title = db.Column(db.String(255), nullable=False, comment='專輯名稱')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='歌手ID')
    cover_url = db.Column(db.Text, nullable=False, comment='專輯封面路徑')
    release_date = db.Column(db.DateTime, nullable=False, comment='建立時間')

    user = db.relationship('User', back_populates='albums')
    songs = db.relationship('Song', back_populates='album')
    album_songs = db.relationship('AlbumSong', back_populates='album')


class AlbumSong(db.Model):
    __tablename__ = 'album_songs'

    album_id = db.Column(db.Integer, db.ForeignKey('albums.album_id'), primary_key=True, nullable=False, comment='專輯ID')
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), primary_key=True, nullable=False, comment='歌曲ID')
    track_num = db.Column(db.Integer, nullable=False, comment='專輯中的第幾首')

    album = db.relationship('Album', back_populates='album_songs')
    song = db.relationship('Song', back_populates='album_songs')