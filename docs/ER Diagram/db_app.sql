
CREATE TABLE album_songs
(
  album_id  INT NOT NULL COMMENT '專輯ID',
  song_id   INT NOT NULL COMMENT '歌曲ID',
  track_num INT NOT NULL COMMENT '專輯中的第幾首',
  PRIMARY KEY (album_id, song_id)
);

CREATE TABLE albums
(
  album_id     INT          NOT NULL COMMENT '專輯ID',
  title        VARCHAR(255) NOT NULL COMMENT '專輯名稱',
  user_id      INT          NOT NULL COMMENT '歌手ID',
  cover_url    TEXT         NOT NULL COMMENT '專輯封面路徑',
  release_data DATETIME     NOT NULL COMMENT '建立時間',
  PRIMARY KEY (album_id)
);

CREATE TABLE playback_queue
(
  queue_id  INT NOT NULL COMMENT '播放佇列ID，PK',
  user_id   INT NOT NULL COMMENT '建立者ID，FK',
  song_id   INT NOT NULL COMMENT '歌曲ID，FK',
  track_num INT NULL     COMMENT '歌曲序數',
  PRIMARY KEY (queue_id)
);

CREATE TABLE playlist_collaborators
(
  queue_id   INT             NOT NULL COMMENT '播放佇列ID，PK，FK',
  user_id    INT             NOT NULL COMMENT '共編使用者ID，PK，FK',
  permission ENUM(edit,view) NULL     COMMENT '權限類型',
  PRIMARY KEY (queue_id, user_id)
);

CREATE TABLE playlist_songs
(
  playlist_id INT NOT NULL COMMENT '歌單ID，FK',
  song_id     INT NOT NULL COMMENT '歌曲ID，FK',
  track_num   INT NULL     COMMENT '歌曲在歌單中的排序位置',
  added_by    INT NULL     COMMENT '加入歌曲的使用者ID，FK',
  PRIMARY KEY (playlist_id, song_id)
);

CREATE TABLE playlists
(
  playlist_id INT          NOT NULL COMMENT '歌單ID',
  user_id     INT          NOT NULL COMMENT '建立者ID',
  title       VARCHAR(255) NOT NULL COMMENT '歌單名稱',
  is_public   BOOLEAN      NOT NULL COMMENT '是否公開',
  PRIMARY KEY (playlist_id)
);

CREATE TABLE realtime_playback
(
  queue_id   INT       NOT NULL COMMENT '播放佇列ID，PK',
  user_id    INT       NOT NULL COMMENT '使用者ID，PK，FK',
  position   INT       NULL     COMMENT '目前播放到第幾首歌',
  started_at TIMESTAMP NULL     COMMENT '開始播放歌曲的時間，用來同步播放狀態',
  PRIMARY KEY (queue_id, user_id)
);

CREATE TABLE songs
(
  song_id   INT          NOT NULL COMMENT '歌曲ID',
  title     VARCHAR(255) NOT NULL COMMENT '歌曲名稱',
  user_id   INT          NOT NULL COMMENT '歌手ID',
  duration  INT          NOT NULL COMMENT '長度',
  file_url  VARCHAR(255) NOT NULL COMMENT '音樂檔案路徑',
  is_public BOOLEAN      NOT NULL COMMENT '是否公開',
  album_id  INT          NULL     COMMENT '專輯ID',
  PRIMARY KEY (song_id)
);

CREATE TABLE user_history
(
  user_id   INT      NOT NULL COMMENT '使用者ID，PK，FK',
  song_id   INT      NOT NULL COMMENT '歌曲ID，FK',
  timestamp DATETIME NOT NULL COMMENT '播放時間',
  PRIMARY KEY (user_id, song_id, timestamp)
);

CREATE TABLE users
(
  user_id       INT                        NOT NULL COMMENT '使用者ID',
  username      VARCHAR(255)               NOT NULL COMMENT '帳號',
  description   TEXT                       NOT NULL COMMENT '簡介',
  email         VARCHAR(255)               NOT NULL COMMENT '信箱',
  password_hash VARCHAR(255)               NOT NULL COMMENT '密碼HASH',
  role          ENUM(user,admin,moderator) NOT NULL COMMENT '權限角色',
  profile_image VARCHAR(255)               NOT NULL COMMENT '頭像',
  created_at    DATETIME                   NOT NULL COMMENT '註冊時間',
  PRIMARY KEY (user_id)
);

ALTER TABLE albums
  ADD CONSTRAINT FK_users_TO_albums
    FOREIGN KEY (user_id)
    REFERENCES users (user_id);

ALTER TABLE album_songs
  ADD CONSTRAINT FK_albums_TO_album_songs
    FOREIGN KEY (album_id)
    REFERENCES albums (album_id);

ALTER TABLE album_songs
  ADD CONSTRAINT FK_songs_TO_album_songs
    FOREIGN KEY (song_id)
    REFERENCES songs (song_id);

ALTER TABLE songs
  ADD CONSTRAINT FK_users_TO_songs
    FOREIGN KEY (user_id)
    REFERENCES users (user_id);

ALTER TABLE songs
  ADD CONSTRAINT FK_albums_TO_songs
    FOREIGN KEY (album_id)
    REFERENCES albums (album_id);

ALTER TABLE playlists
  ADD CONSTRAINT FK_users_TO_playlists
    FOREIGN KEY (user_id)
    REFERENCES users (user_id);

ALTER TABLE playlist_songs
  ADD CONSTRAINT FK_playlists_TO_playlist_songs
    FOREIGN KEY (playlist_id)
    REFERENCES playlists (playlist_id);

ALTER TABLE playlist_songs
  ADD CONSTRAINT FK_songs_TO_playlist_songs
    FOREIGN KEY (song_id)
    REFERENCES songs (song_id);

ALTER TABLE playlist_songs
  ADD CONSTRAINT FK_users_TO_playlist_songs
    FOREIGN KEY (added_by)
    REFERENCES users (user_id);

ALTER TABLE user_history
  ADD CONSTRAINT FK_users_TO_user_history
    FOREIGN KEY (user_id)
    REFERENCES users (user_id);

ALTER TABLE user_history
  ADD CONSTRAINT FK_songs_TO_user_history
    FOREIGN KEY (song_id)
    REFERENCES songs (song_id);

ALTER TABLE playback_queue
  ADD CONSTRAINT FK_users_TO_playback_queue
    FOREIGN KEY (user_id)
    REFERENCES users (user_id);

ALTER TABLE playback_queue
  ADD CONSTRAINT FK_songs_TO_playback_queue
    FOREIGN KEY (song_id)
    REFERENCES songs (song_id);

ALTER TABLE realtime_playback
  ADD CONSTRAINT FK_playback_queue_TO_realtime_playback
    FOREIGN KEY (queue_id)
    REFERENCES playback_queue (queue_id);

ALTER TABLE realtime_playback
  ADD CONSTRAINT FK_users_TO_realtime_playback
    FOREIGN KEY (user_id)
    REFERENCES users (user_id);

ALTER TABLE playlist_collaborators
  ADD CONSTRAINT FK_playback_queue_TO_playlist_collaborators
    FOREIGN KEY (queue_id)
    REFERENCES playback_queue (queue_id);

ALTER TABLE playlist_collaborators
  ADD CONSTRAINT FK_users_TO_playlist_collaborators
    FOREIGN KEY (user_id)
    REFERENCES users (user_id);
