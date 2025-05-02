from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Song(Base):
    __tablename__ = 'songs'

    song_id = Column(Integer, primary_key=True, nullable=False, comment='歌曲ID')
    title = Column(String(255), nullable=False, comment='歌曲名稱')
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment='歌手ID')
    duration = Column(Integer, nullable=False, comment='長度')
    file_url = Column(String(255), nullable=False, comment='音樂檔案路徑')
    is_public = Column(Boolean, nullable=False, comment='是否公開')
    album_id = Column(Integer, ForeignKey('albums.album_id'), nullable=True, comment='專輯ID')

    user = relationship('User', back_populates='songs')
    album = relationship('Album', back_populates='songs')
    album_songs = relationship('AlbumSong', back_populates='song')
    playlist_songs = relationship('PlaylistSong', back_populates='song')
    user_history = relationship('UserHistory', back_populates='song')
    playback_queue = relationship('PlaybackQueue', back_populates='song')
