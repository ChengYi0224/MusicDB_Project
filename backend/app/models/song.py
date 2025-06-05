# backend/app/models/song.py
from app.extensions import db

class Song(db.Model):
    __tablename__ = 'songs'

    song_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='歌曲ID')
    title = db.Column(db.String(255), nullable=False, comment='歌曲名稱')
    # user_id 欄位，代表歌曲的演唱者/創作者
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, comment='歌手ID')
    duration = db.Column(db.Integer, nullable=False, comment='長度')
    file_url = db.Column(db.String(255), nullable=False, comment='音樂檔案路徑')
    is_public = db.Column(db.Boolean, nullable=False, comment='是否公開')

    # 歌曲的演唱者/創作者 (User) - 名稱保持為 'user'
    # 假設 User 模型中有一個名為 'songs' 的 relationship 與此對應
    user = db.relationship('User', back_populates='songs') 

    # 多對多關係：一首歌可以屬於多張專輯
    # 透過 'album_songs' 中介表連接到 Album 模型
    albums = db.relationship(
        'Album',
        secondary='album_songs',  # 指定中介資料表的名稱
        back_populates='songs'    # 對應 Album 模型中 'songs' relationship 的 back_populates
    )

    # 連接到 AlbumSong 中介模型的 relationship
    # 用於直接訪問中介物件 (例如獲取 track_num 等 AlbumSong 表上的額外欄位)
    # 原 'album_songs' 更名為 'album_song_entries' 以更清晰地區分其用途
    album_song_entries = db.relationship(
        'AlbumSong', 
        back_populates='song', # 對應 AlbumSong 模型中 'song' relationship 的 back_populates
        cascade="all, delete-orphan" # 當 Song 被刪除時，相關的 AlbumSong 記錄也一併刪除
    )

    # 連接到 PlaylistSong 中介模型的 relationship
    playlist_songs = db.relationship(
        'PlaylistSong', 
        back_populates='song', # 對應 PlaylistSong 模型中 'song' relationship 的 back_populates
        cascade="all, delete-orphan" # 當 Song 被刪除時，相關的 PlaylistSong 記錄也一併刪除
    )

    # 連接到 UserHistory 模型的 relationship
    user_history = db.relationship(
        'UserHistory', 
        back_populates='song', # 對應 UserHistory 模型中 'song' relationship 的 back_populates
        cascade="all, delete-orphan" # 當 Song 被刪除時，相關的 UserHistory 記錄也一併刪除
    )

    # 連接到 PlaybackQueue 模型的 relationship
    # cascade 行為根據您的業務邏輯決定 (如果歌曲被刪除，是否也刪除佇列中的項目)
    playback_queue = db.relationship(
        'PlaybackQueue', 
        back_populates='song' # 對應 PlaybackQueue 模型中 'song' relationship 的 back_populates
    )

    def __repr__(self):
        return f'<Song {self.title}>'