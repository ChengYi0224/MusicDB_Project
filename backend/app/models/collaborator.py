from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base

class PlaylistCollaborator(Base):
    __tablename__ = 'playlist_collaborators'

    queue_id = Column(Integer, ForeignKey('playback_queue.queue_id'), primary_key=True, nullable=False, comment='播放佇列ID')
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True, nullable=False, comment='共編使用者ID')
    permission = Column(Enum('edit', 'view'), nullable=True, comment='權限類型')

    queue = relationship('PlaybackQueue', back_populates='playlist_collaborators')
    user = relationship('User', back_populates='playlist_collaborations')
