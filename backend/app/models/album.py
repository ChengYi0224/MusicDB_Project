# album.py
from app.extensions import db

class Album(db.Model):
    __tablename__ = 'albums'

    album_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='專輯ID')
    title = db.Column(db.String(255), nullable=False, comment='專輯名稱')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='歌手ID')
    cover_url = db.Column(db.Text, nullable=False, comment='專輯封面路徑')
    release_date = db.Column(db.DateTime, nullable=False, comment='建立時間')

    # 專輯的創作者/歌手
    user = db.relationship('User', back_populates='albums') # 假設 User 模型有 'albums' relationship

    songs = db.relationship(
        'Song',
        secondary='album_songs',  # 指定中介資料表的名稱
        back_populates='albums'   # 對應 Song 模型中 'albums' relationship 的 back_populates
    )

    # 連接到 AlbumSong 中介模型的 relationship
    # 用於直接訪問中介物件 (例如獲取 track_num 等 AlbumSong 表上的額外欄位)
    album_song_entries = db.relationship(
        'AlbumSong', 
        back_populates='album',  # 對應 AlbumSong 模型中 'album' relationship 的 back_populates
        cascade="all, delete-orphan" # 當 Album 被刪除時，相關的 AlbumSong 記錄也一併刪除
    )
    
    # album_songs_association = db.relationship('AlbumSong', back_populates='album', cascade="all, delete-orphan") # <--- 這個是重複的，可以移除

class AlbumSong(db.Model):
    __tablename__ = 'album_songs'

    album_id = db.Column(db.Integer, db.ForeignKey('albums.album_id'), primary_key=True, nullable=False, comment='專輯ID')
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), primary_key=True, nullable=False, comment='歌曲ID')
    track_num = db.Column(db.Integer, nullable=False, comment='專輯中的第幾首')

    # back_populates 應對應 Album 模型中與 AlbumSong 關聯的屬性名
    album = db.relationship('Album', back_populates='album_song_entries') 
    # back_populates 應對應 Song 模型中與 AlbumSong 關聯的屬性名
    song = db.relationship('Song', back_populates='album_song_entries')