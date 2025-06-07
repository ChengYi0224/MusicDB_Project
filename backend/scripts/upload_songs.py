# backend/scripts/upload_browse_songs.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ast
import config

from app import create_app
from app.extensions import db
from app.models import Song
from app.utils.network import Check_IPv6_Dialogue
from crawler.crawlers import print_info, print_success, print_error, print_warning
from scripts.supabase_handler import (
    initialize_supabase_client,
    find_or_create_artist,
    upload_file_to_storage,
    cleanup_local_file
)

# --- 設定 ---
# 這個腳本要讀取的爬蟲結果檔案
CRAWLER_OUTPUT_FILE = config.BROWSE_CRAWLER_OUTPUT_FILE

def process_browse_songs():
    """主處理函式"""
    if not os.path.exists(CRAWLER_OUTPUT_FILE):
        print_error(f"找不到爬蟲結果檔案: {CRAWLER_OUTPUT_FILE}")
        return

    app = create_app()
    with app.app_context():
        supabase_client = initialize_supabase_client(app)
        if not supabase_client:
            return

        new_songs_count = 0
        
        with open(CRAWLER_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    song_data = ast.literal_eval(line.strip())
                except (ValueError, SyntaxError) as e:
                    print_warning(f"無法解析行: {line.strip()} - 錯誤: {e}")
                    continue

                try:
                    song_id_str = song_data.get('song_id')
                    if not song_id_str: continue

                    # 1. 檢查歌曲是否已在本地資料庫存在
                    existing_song = Song.query.filter_by(song_id=int(song_id_str)).first()
                    if existing_song:
                        print_info(f"歌曲 '{song_data.get('title')}' 已在資料庫中，跳過。")
                        continue

                    # 2. 尋找或建立演出者 (User)
                    artist = find_or_create_artist(song_data.get('artist_name'))
                    if not artist: continue

                    # 3. 上傳檔案到 Supabase Storage
                    local_path = song_data.get('local_file_path')
                    if not local_path or not os.path.exists(local_path):
                        print_warning(f"找不到本地檔案: {local_path}，跳過歌曲 '{song_data.get('title')}'。")
                        continue

                    # 動態獲取副檔名
                    _, file_extension = os.path.splitext(local_path)
                    
                    # 組合新的、正確的 storage_path
                    storage_path = f"songs/{artist.user_id}/{song_id_str}{file_extension}"
                    public_url = upload_file_to_storage(supabase_client, local_path, storage_path)
                    if not public_url: continue

                    # 4. 建立 Song 物件並準備存入資料庫
                    new_song = Song(
                        song_id=int(song_id_str),
                        title=song_data.get('title'),
                        user_id=artist.user_id,
                        duration=song_data.get('duration_seconds') or 0,
                        file_url=public_url,
                        is_public=True
                    )
                    db.session.add(new_song)
                    new_songs_count += 1
                    print_success(f"準備新增歌曲到資料庫: '{new_song.title}'")

                    # 5. 清理本地暫存檔案
                    cleanup_local_file(local_path)

                except Exception as e:
                    print_error(f"處理歌曲 '{song_data.get('title')}' 時發生嚴重錯誤: {e}")
                    db.session.rollback()

        if new_songs_count > 0:
            try:
                db.session.commit()
                print_success(f"成功提交 {new_songs_count} 首新歌曲到資料庫！")
            except Exception as e:
                db.session.rollback()
                print_error(f"最終提交資料庫時發生錯誤: {e}")
        else:
            print_info("沒有新的歌曲需要新增。")

if __name__ == "__main__":
    if Check_IPv6_Dialogue():
        process_browse_songs()