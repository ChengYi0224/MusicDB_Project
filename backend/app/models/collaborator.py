from database.session import db

class PlaylistCollaborator(db.Model):
    __tablename__ = 'playlist_collaborators'

    queue_id = db.Column(db.Integer, db.ForeignKey('playback_queue.queue_id'), primary_key=True, nullable=False, comment='播放佇列ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False, comment='共編使用者ID')
    permission = db.Column(db.Enum('edit', 'view'), nullable=True, comment='權限類型')

    queue = db.relationship('PlaybackQueue', back_populates='playlist_collaborators')
    user = db.relationship('User', back_populates='playlist_collaborations')
