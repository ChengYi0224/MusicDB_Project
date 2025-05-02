from database.session import db

class Playlist(db.Model):
    
    __tablename__ = 'playlists'

    playlist_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='歌單ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='建立者ID')
    title = db.Column(db.String(255), nullable=False, comment='歌單名稱')
    is_public = db.Column(db.Boolean, nullable=False, comment='是否公開')

    user = db.relationship('User', back_populates='playlists')
    playlist_songs = db.relationship('PlaylistSong', back_populates='playlist')