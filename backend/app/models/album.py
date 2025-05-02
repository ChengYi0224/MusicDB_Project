from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Album(Base):
    __tablename__ = 'albums'

    album_id = Column(Integer, primary_key=True, nullable=False, comment='專輯ID')
    title = Column(String(255), nullable=False, comment='專輯名稱')
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment='歌手ID')
    cover_url = Column(Text, nullable=False, comment='專輯封面路徑')
    release_data = Column(DateTime, nullable=False, comment='建立時間')

    user = relationship('User', back_populates='albums')
    songs = relationship('Song', back_populates='album')
    album_songs = relationship('AlbumSong', back_populates='album')


class AlbumSong(Base):
    __tablename__ = 'album_songs'

    album_id = Column(Integer, ForeignKey('albums.album_id'), primary_key=True, nullable=False, comment='專輯ID')
    song_id = Column(Integer, ForeignKey('songs.song_id'), primary_key=True, nullable=False, comment='歌曲ID')
    track_num = Column(Integer, nullable=False, comment='專輯中的第幾首')

    album = relationship('Album', back_populates='album_songs')
    song = relationship('Song', back_populates='album_songs')