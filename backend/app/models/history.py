from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class UserHistory(Base):
    __tablename__ = 'user_history'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True, nullable=False, comment='使用者ID')
    song_id = Column(Integer, ForeignKey('songs.song_id'), primary_key=True, nullable=False, comment='歌曲ID')
    timestamp = Column(DateTime, primary_key=True, nullable=False, comment='播放時間')

    user = relationship('User', back_populates='user_history')
    song = relationship('Song', back_populates='user_history')
