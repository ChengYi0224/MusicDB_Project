from database.session import db

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='使用者ID')
    username = db.Column(db.String(255), nullable=False, comment='帳號')
    description = db.Column(db.Text, nullable=False, comment='簡介')
    email = db.Column(db.String(255), nullable=False, comment='信箱')
    password_hash = db.Column(db.String(255), nullable=False, comment='密碼HASH')
    role = db.Column(db.Enum('admin', 'artist', 'user'), nullable=False, comment='權限角色')
    profile_image = db.Column(db.String(255), nullable=False, comment='頭像')
    created_at = db.Column(db.DateTime, nullable=False, comment='註冊時間')

    # Relationships
    albums = db.relationship('Album', back_populates='user')
    songs = db.relationship('Song', back_populates='user')
    playlists = db.relationship('Playlist', back_populates='user')
    playlist_songs = db.relationship('PlaylistSong', back_populates='added_by_user')
    user_history = db.relationship('UserHistory', back_populates='user')
    playback_queue = db.relationship('PlaybackQueue', back_populates='user')
    realtime_playback = db.relationship('RealtimePlayback', back_populates='user')
    playlist_collaborations = db.relationship('PlaylistCollaborator', back_populates='user')
