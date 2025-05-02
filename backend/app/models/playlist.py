from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Playlist(Base):
    __tablename__ = 'playlists'

    playlist_id = Column(Integer, primary_key=True, nullable=False, comment='歌單ID')
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment='建立者ID')
    title = Column(String(255), nullable=False, comment='歌單名稱')
    is_public = Column(Boolean, nullable=False, comment='是否公開')

    user = relationship('User', back_populates='playlists')
    playlist_songs = relationship('PlaylistSong', back_populates='playlist')