from app.extensions import db

class PlaybackQueue(db.Model):
    __tablename__ = 'playback_queue'

    queue_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='播放佇列ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='建立者ID')
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), nullable=False, comment='歌曲ID')
    track_num = db.Column(db.Integer, nullable=True, comment='歌曲序數')

    user = db.relationship('User', back_populates='playback_queue')
    song = db.relationship('Song', back_populates='playback_queue')
    realtime_playback = db.relationship('RealtimePlayback', back_populates='queue', uselist=False)
    playlist_collaborators = db.relationship('PlaylistCollaborator', back_populates='queue')
