-- 專輯表
CREATE TABLE albums (
  album_id     INT      NOT NULL COMMENT '專輯ID',
  title        VARCHAR(255)  NOT NULL COMMENT '專輯名稱',
  user_id      INT      NOT NULL COMMENT '歌手ID',
  cover_url    TEXT     NOT NULL COMMENT '專輯封面路徑',
  release_data DATETIME NOT NULL COMMENT '建立時間',
  PRIMARY KEY (album_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
) COMMENT='專輯表';

-- 專輯收錄歌曲表
CREATE TABLE album_songs (
  album_id  INT NOT NULL COMMENT '專輯ID',
  song_id   INT NOT NULL COMMENT '歌曲ID',
  track_num INT NOT NULL COMMENT '專輯中的第幾首',
  PRIMARY KEY (album_id, song_id),
  FOREIGN KEY (album_id) REFERENCES albums(album_id),
  FOREIGN KEY (song_id) REFERENCES songs(song_id)
) COMMENT='專輯收錄歌曲表';

-- 歌曲表
CREATE TABLE songs (
  song_id   INT     NOT NULL COMMENT '歌曲ID',
  title     VARCHAR(255) NOT NULL COMMENT '歌曲名稱',
  user_id   INT     NOT NULL COMMENT '歌手ID',
  duration  INT     NOT NULL COMMENT '長度',
  file_url  VARCHAR(255) NOT NULL COMMENT '音樂檔案路徑',
  is_public BOOLEAN NOT NULL COMMENT '是否公開',
  PRIMARY KEY (song_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
) COMMENT='歌曲表';

-- 使用者表
CREATE TABLE users (
  user_id       INT      NOT NULL COMMENT '使用者ID',
  username      VARCHAR(255)  NOT NULL COMMENT '帳號',
  description   TEXT     NOT NULL COMMENT '簡介',
  email         VARCHAR(255)  NOT NULL COMMENT '信箱',
  password_hash VARCHAR(255)  NOT NULL COMMENT '密碼HASH',
  role          ENUM('admin', 'artist', 'user') NOT NULL COMMENT '權限角色',
  profile_image VARCHAR(255)  NOT NULL COMMENT '頭像',
  created_at    DATETIME NOT NULL COMMENT '註冊時間',
  PRIMARY KEY (user_id)
) COMMENT='使用者帳號表';

-- 歌單表
CREATE TABLE playlists (
  playlist_id INT     NOT NULL COMMENT '歌單ID',
  user_id     INT     NOT NULL COMMENT '建立者ID',
  title       VARCHAR(255) NOT NULL COMMENT '歌單名稱',
  is_public   BOOLEAN NOT NULL COMMENT '是否公開',
  PRIMARY KEY (playlist_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
) COMMENT='歌單表';

-- 歌單內歌曲
CREATE TABLE playlist_songs (
  playlist_id INT NOT NULL COMMENT '歌單ID，FK',
  song_id     INT NOT NULL COMMENT '歌曲ID，FK',
  track_num   INT COMMENT '歌曲在歌單中的排序位置',
  added_by    INT COMMENT '加入歌曲的使用者ID，FK',
  PRIMARY KEY (playlist_id, song_id),
  FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
  FOREIGN KEY (song_id) REFERENCES songs(song_id),
  FOREIGN KEY (added_by) REFERENCES users(user_id)
) COMMENT='歌單內歌曲對應表';

-- 聆聽紀錄
CREATE TABLE user_history (
  user_id   INT NOT NULL COMMENT '使用者ID，PK，FK',
  song_id   INT NOT NULL COMMENT '歌曲ID，FK',
  timestamp DATETIME NOT NULL COMMENT '播放時間',
  PRIMARY KEY (user_id, song_id, timestamp),
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (song_id) REFERENCES songs(song_id)
) COMMENT='使用者聆聽紀錄';

-- 播放佇列
CREATE TABLE playback_queue (
  queue_id  INT NOT NULL COMMENT '播放佇列ID，PK',
  user_id   INT NOT NULL COMMENT '建立者ID，FK',
  song_id   INT NOT NULL COMMENT '歌曲ID，FK',
  track_num INT COMMENT '歌曲序數',
  PRIMARY KEY (queue_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (song_id) REFERENCES songs(song_id)
) COMMENT='播放佇列內容';

-- 即時播放狀態
CREATE TABLE realtime_playback (
  queue_id   INT NOT NULL COMMENT '播放佇列ID，PK',
  user_id    INT NOT NULL COMMENT '使用者ID，PK，FK',
  position   INT COMMENT '目前播放到第幾首歌',
  started_at TIMESTAMP COMMENT '開始播放歌曲的時間，用來同步播放狀態',
  PRIMARY KEY (queue_id, user_id),
  FOREIGN KEY (queue_id) REFERENCES playback_queue(queue_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
) COMMENT='即時播放狀態資訊';

-- 歌單共編
CREATE TABLE playlist_collaborators (
  playlist_id  INT NOT NULL COMMENT '播放清單ID，PK，FK',
  user_id   INT NOT NULL COMMENT '共編使用者ID，PK，FK',
  permission ENUM('edit', 'view') COMMENT '權限類型',
  PRIMARY KEY (queue_id, user_id),
  FOREIGN KEY (playlist_id) REFERENCES playback(playlist_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id)
) COMMENT='歌單共編資訊';
