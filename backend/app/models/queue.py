from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class PlaybackQueue(Base):
    __tablename__ = 'playback_queue'

    queue_id = Column(Integer, primary_key=True, nullable=False, comment='播放佇列ID')
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, comment='建立者ID')
    song_id = Column(Integer, ForeignKey('songs.song_id'), nullable=False, comment='歌曲ID')
    track_num = Column(Integer, nullable=True, comment='歌曲序數')

    user = relationship('User', back_populates='playback_queue')
    song = relationship('Song', back_populates='playback_queue')
    realtime_playback = relationship('RealtimePlayback', back_populates='queue', uselist=False)
    playlist_collaborators = relationship('PlaylistCollaborator', back_populates='queue')
