from app.extensions import db
from sqlalchemy.ext.associationproxy import association_proxy

class Song(db.Model):
    __tablename__ = 'songs'

    song_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    is_public = db.Column(db.Boolean, nullable=False, default=True)

    # 與 User 的關係
    user = db.relationship('User', back_populates='songs')

    # 與 Album 的多對多關係
    album_entries = db.relationship('AlbumSong', back_populates='song', cascade="all, delete-orphan")
    albums = association_proxy('album_entries', 'album')

    # 與 Playlist 的多對多關係
    playlist_entries = db.relationship('PlaylistSong', back_populates='song', cascade="all, delete-orphan")
    playlists = association_proxy('playlist_entries', 'playlist')
    
    user_history = db.relationship('UserHistory', back_populates='song', cascade="all, delete-orphan")
    playback_queue = db.relationship('PlaybackQueue', back_populates='song')

    def __repr__(self):
        return f'<Song {self.title}>'