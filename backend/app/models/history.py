from app.extensions import db

class UserHistory(db.Model):
    __tablename__ = 'user_history'

    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable=False, comment='使用者ID')
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), primary_key=True, nullable=False, comment='歌曲ID')
    timestamp = db.Column(db.DateTime, primary_key=True, nullable=False, comment='播放時間')

    user = db.relationship('User', back_populates='user_history')
    song = db.relationship('Song', back_populates='user_history')
