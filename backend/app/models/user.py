# backend/app/models/user.py
from app.extensions import db
import enum
from sqlalchemy import Enum
from sqlalchemy.sql import func
# 導入密碼雜湊輔助函數
from app.utils.security import DEFAULT_PASSWORD_HASH

class enumRole(enum.Enum):
    admin = 'admin'
    artist = 'artist'
    moderator = 'moderator'
    user = 'user'

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='使用者ID')
    username = db.Column(db.String(255), nullable=False, unique=True, comment='帳號')
    email = db.Column(db.String(255), nullable=True, unique=True, comment='信箱')
    password_hash = db.Column(db.String(255), nullable=False, default=DEFAULT_PASSWORD_HASH, comment='密碼HASH')
    description = db.Column(db.Text, nullable=True, default="這位演出者尚未留下任何介紹。", comment='簡介')
    role = db.Column(Enum(enumRole, name = "enumRole"), nullable=False, default=enumRole.user, comment='權限角色')
    profile_image = db.Column(db.String(255), nullable=True, comment='頭像')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, comment='註冊時間')

    # Relationships
    albums = db.relationship('Album', back_populates='user')
    songs = db.relationship('Song', back_populates='user')
    playlists = db.relationship('Playlist', back_populates='user')
    added_playlist_entries = db.relationship('PlaylistSong', back_populates='added_by_user')
    user_history = db.relationship('UserHistory', back_populates='user')
    playback_queue = db.relationship('PlaybackQueue', back_populates='user')
    realtime_playback = db.relationship('RealtimePlayback', back_populates='user')
    playlist_collaborations = db.relationship('PlaylistCollaborator', back_populates='user')
