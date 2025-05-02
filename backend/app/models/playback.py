from database.session import db

class RealtimePlayback(db.Model):
    __tablename__ = 'realtime_playback'

    queue_id = db.Column(db.Integer, db.ForeignKey('playback_queue.queue_id'), primary_key=True, nullable=False, comment='播放佇列ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False, comment='使用者ID')
    position = db.Column(db.Integer, nullable=True, comment='目前播放到第幾首歌')
    started_at = db.Column(db.TIMESTAMP, nullable=True, comment='開始播放歌曲的時間，用來同步播放狀態')

    queue = db.relationship('PlaybackQueue', back_populates='realtime_playback')
    user = db.relationship('User', back_populates='realtime_playback')
