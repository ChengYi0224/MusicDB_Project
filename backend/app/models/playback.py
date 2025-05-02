from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from .base import Base

class RealtimePlayback(Base):
    __tablename__ = 'realtime_playback'

    queue_id = Column(Integer, ForeignKey('playback_queue.queue_id'), primary_key=True, nullable=False, comment='播放佇列ID')
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True, nullable=False, comment='使用者ID')
    position = Column(Integer, nullable=True, comment='目前播放到第幾首歌')
    started_at = Column(TIMESTAMP, nullable=True, comment='開始播放歌曲的時間，用來同步播放狀態')

    queue = relationship('PlaybackQueue', back_populates='realtime_playback')
    user = relationship('User', back_populates='realtime_playback')
