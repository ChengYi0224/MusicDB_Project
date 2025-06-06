#models/playlist_song.py
from app.extensions import db
from sqlalchemy import UniqueConstraint

class PlaylistSong(db.Model):
    __tablename__ = 'playlist_songs'

    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.playlist_id'), primary_key=True, nullable=False, comment='歌單ID')
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), primary_key=True, nullable=False, comment='歌曲ID')
    track_num = db.Column(db.Integer, nullable=False, comment='歌曲在歌單中的排序位置')
    added_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True, comment='加入歌曲的使用者ID')

    playlist = db.relationship('Playlist', back_populates='playlist_songs')
    song = db.relationship('Song', back_populates='playlist_songs')
    added_by_user = db.relationship('User', back_populates='playlist_songs')

    __table_args__ = (
        UniqueConstraint('playlist_id', 'track_num', name='_playlist_track_uc'),
    )