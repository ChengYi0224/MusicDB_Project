from app.extensions import db

import enum
from sqlalchemy import Enum

class enumPermision(enum.Enum):
    edit = 'edit'
    view = 'view'

class PlaylistCollaborator(db.Model):
    __tablename__ = 'playlist_collaborators'

    queue_id = db.Column(db.Integer, db.ForeignKey('playback_queue.queue_id'), primary_key=True, nullable=False, comment='播放佇列ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False, comment='共編使用者ID')
    permission = db.Column(Enum(enumPermision, name = "enumPermision"), nullable=False, comment='權限類型')

    queue = db.relationship('PlaybackQueue', back_populates='playlist_collaborators')
    user = db.relationship('User', back_populates='playlist_collaborations')
