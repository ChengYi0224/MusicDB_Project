from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class PlaylistSong(Base):
    __tablename__ = 'playlist_songs'

    playlist_id = Column(Integer, ForeignKey('playlists.playlist_id'), primary_key=True, nullable=False, comment='歌單ID')
    song_id = Column(Integer, ForeignKey('songs.song_id'), primary_key=True, nullable=False, comment='歌曲ID')
    track_num = Column(Integer, nullable=True, comment='歌曲在歌單中的排序位置')
    added_by = Column(Integer, ForeignKey('users.user_id'), nullable=True, comment='加入歌曲的使用者ID')

    playlist = relationship('Playlist', back_populates='playlist_songs')
    song = relationship('Song', back_populates='playlist_songs')
    added_by_user = relationship('User', back_populates='playlist_songs')