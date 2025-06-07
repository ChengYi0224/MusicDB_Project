# backend/scripts/upload_playlists.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import ast
from collections import defaultdict

import config

from app import create_app
from app.extensions import db
# 確保你導入的是更新後的模型
from app.models import Song, Playlist, PlaylistSong, User
from app.utils.network import Check_IPv6_Dialogue
from crawler.crawlers import print_info, print_success, print_error, print_warning
from scripts.supabase_handler import (
    initialize_supabase_client,
    find_or_create_artist,
    upload_file_to_storage,
    cleanup_local_file
)

# --- 設定 ---
CRAWLER_OUTPUT_FILE = config.PLAYLIST_CRAWLER_OUTPUT_FILE

def process_playlists():
    """主處理函式"""
    if not os.path.exists(CRAWLER_OUTPUT_FILE):
        print_error(f"找不到爬蟲結果檔案: {CRAWLER_OUTPUT_FILE}")
        return

    # 1. 讀取所有資料並按歌單分組
    playlists_data = defaultdict(list)
    with open(CRAWLER_OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                song_data = ast.literal_eval(line.strip())
                playlist_key = song_data.get('playlist_url')
                if playlist_key:
                    playlists_data[playlist_key].append(song_data)
            except (ValueError, SyntaxError):
                continue
    
    if not playlists_data:
        print_warning("結果檔案中沒有可處理的歌單資料。")
        return

    app = create_app()
    with app.app_context():
        supabase_client = initialize_supabase_client(app)
        if not supabase_client: return

        # 2. 遍歷每一個歌單進行處理
        for playlist_url, songs_in_playlist in playlists_data.items():
            playlist_info = songs_in_playlist[0]
            playlist_title = playlist_info.get('playlist_title')
            
            try:
                print_info(f"\n--- 開始處理歌單: {playlist_title} ---")

                # 3. 檢查歌單是否已存在 (以標題為依據)
                if Playlist.query.filter_by(title=playlist_title).first():
                    print_info(f"歌單 '{playlist_title}' 已在資料庫中，跳過。")
                    continue
                
                # 4. 尋找或建立歌單的建立者 (假設是第一首歌的演出者)
                creator = find_or_create_artist(playlist_info.get('artist_name'))
                if not creator:
                    print_warning(f"無法為歌單 '{playlist_title}' 找到建立者，跳過。")
                    continue

                # 5. 建立新的 Playlist 物件
                new_playlist = Playlist(
                    user_id=creator.user_id,
                    title=playlist_title,
                    is_public=True
                )
                db.session.add(new_playlist)
                # 我們不再需要 db.session.flush()，因為我們會在最後才 commit
                
                print_success(f"準備新增歌單 '{playlist_title}'...")

                # 6. 內層迴圈：處理歌單下的每一首歌
                for track_index, song_data in enumerate(songs_in_playlist, 1):
                    song_id_str = song_data.get('song_id')
                    if not song_id_str: continue

                    # 6a. 尋找或建立 Song 物件
                    song_in_db = Song.query.filter_by(song_id=int(song_id_str)).first()
                    if not song_in_db:
                        # 如果歌曲不存在，則建立它
                        artist = find_or_create_artist(song_data.get('artist_name'))
                        if not artist: continue
                        
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

                        song_in_db = Song(
                            song_id=int(song_id_str),
                            title=song_data.get('title'),
                            user_id=artist.user_id,
                            duration=song_data.get('duration_seconds') or 0,
                            file_url=public_url,
                            is_public=True
                        )
                        db.session.add(song_in_db)
                        cleanup_local_file(local_path)
                    
                    # 6b. 【核心】手動建立 PlaylistSong 這張「關聯申請表」
                    #    這是與新模型配合的正確做法
                    #    我們直接將物件關聯起來，而不是只用 ID
                    new_playlist_song_entry = PlaylistSong(
                        playlist=new_playlist,
                        song=song_in_db,
                        track_num=song_data.get('track_num') or track_index,
                        added_by_user=creator
                    )
                    db.session.add(new_playlist_song_entry)

                print_info(f"歌單 '{playlist_title}' 下的所有歌曲已準備完畢。")

            except Exception as e:
                print_error(f"處理歌單 '{playlist_title}' 時發生嚴重錯誤: {e}")
                db.session.rollback() # 如果單一歌單出錯，只回滾這個歌單的變動
        
        # 7. 所有歌單都處理完畢後，一次性提交
        try:
            db.session.commit()
            print_success(f"成功提交所有新歌單與歌曲到資料庫！")
        except Exception as e:
            db.session.rollback()
            print_error(f"最終提交資料庫時發生錯誤: {e}")

if __name__ == "__main__":
    if Check_IPv6_Dialogue():
        process_playlists()