from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, nullable=False, comment='使用者ID')
    username = Column(String(255), nullable=False, comment='帳號')
    description = Column(Text, nullable=False, comment='簡介')
    email = Column(String(255), nullable=False, comment='信箱')
    password_hash = Column(String(255), nullable=False, comment='密碼HASH')
    role = Column(Enum('admin', 'artist', 'user'), nullable=False, comment='權限角色')
    profile_image = Column(String(255), nullable=False, comment='頭像')
    created_at = Column(DateTime, nullable=False, comment='註冊時間')

    # Relationships
    albums = relationship('Album', back_populates='user')
    songs = relationship('Song', back_populates='user')
    playlists = relationship('Playlist', back_populates='user')
    playlist_songs = relationship('PlaylistSong', back_populates='added_by_user')
    user_history = relationship('UserHistory', back_populates='user')
    playback_queue = relationship('PlaybackQueue', back_populates='user')
    realtime_playback = relationship('RealtimePlayback', back_populates='user')
    playlist_collaborations = relationship('PlaylistCollaborator', back_populates='user')
