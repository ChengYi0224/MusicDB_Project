import os
import sys
import uuid

# --- 1. 設定與匯入 ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app import create_app
from app.extensions import db
from app.models import Song, User
from app.models.user import enumRole # 導入角色 Enum
from crawler.hls_crawler import run_song_crawler, print_info, print_success, print_error, print_warning
from supabase import create_client, Client
from app.utils import Has_IPv6_Addr

def upload_crawled_data():
    app = create_app()
    with app.app_context():
        # --- 2. 建立 Supabase Storage 客戶端 ---
        supabase_url = app.config.get("SUPABASE_URL")
        supabase_key = app.config.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            print_error("Supabase URL 或 Key 未在 Flask config 中設定。")
            return
        supabase_storage_client: Client = create_client(supabase_url, supabase_key)
        BUCKET_NAME = "song-files" # 請確保您已在 Supabase 後台建立這個儲存桶

        # --- 3. 執行爬蟲，並要求下載檔案 ---
        print_info("準備執行爬蟲並下載暫存檔案...")
        crawled_songs = run_song_crawler(
            max_songs_to_crawl=20,
            perform_download_and_save=True # ★★★ 設為 True 來執行下載 ★★★
        )
        if not crawled_songs:
            print_warning("爬蟲未返回任何資料，結束執行。")
            return

        new_songs_count = 0
        for song_data in crawled_songs:
            try:
                # --- 4. 檢查歌曲是否已存在 ---
                song_id_str = song_data.get('song_id')
                if not song_id_str: continue
                
                existing_song = db.session.query(Song).filter_by(song_id=int(song_id_str)).first()
                if existing_song:
                    print_info(f"歌曲 '{song_data.get('title')}' 已存在，跳過。")
                    continue

                # --- 5. 處理 User (查詢或建立) ---
                artist_name = song_data.get('artist_name')
                user = db.session.query(User).filter_by(username=artist_name).first()
                if not user:
                    print_info(f"演出者 '{artist_name}' 不存在，正在建立新使用者...")
                    user = User(
                        username=artist_name,
                        email=None, # 模型允許 email 為空
                        role=enumRole.artist # 明確指定角色為演出者
                    )
                    db.session.add(user)
                    db.session.flush() # flush 以便立即獲取 user.user_id

                # --- 6. 上傳檔案到 Supabase Storage ---
                local_path = song_data.get('local_file_path')
                if not local_path or not os.path.exists(local_path):
                    print_warning(f"歌曲 '{song_data.get('title')}' 缺少本地檔案，無法上傳。")
                    continue
                
                storage_path = f"songs/{user.user_id}/{song_id_str}.ts"
                print_info(f"正在上傳 '{local_path}' 到 Storage...")
                with open(local_path, 'rb') as f:
                    supabase_storage_client.storage.from_(BUCKET_NAME).upload(
                        path=storage_path,
                        file=f,
                        file_options={"content-type": "video/mp2t", "upsert": "true"}
                    )
                
                # --- 7. 取得公開 URL ---
                public_url = supabase_storage_client.storage.from_(BUCKET_NAME).get_public_url(storage_path)

                # --- 8. 建立 Song 物件並存入資料庫 (修正對應欄位) ---
                new_song = Song(
                    song_id=int(song_id_str),
                    title=song_data.get('title'),
                    user_id=user.user_id, # ★★★ 使用查詢到的 user_id ★★★
                    duration=song_data.get('duration_seconds'), # 對應 'duration' 欄位
                    file_url=public_url, # 使用 Storage 的 URL
                    is_public=True
                )
                db.session.add(new_song)
                new_songs_count += 1

                # --- 9. 清理本地暫存檔案 ---
                os.remove(local_path)
                print_success(f"成功處理歌曲 '{new_song.title}' 並清理本地檔案。")

            except Exception as e:
                print_error(f"處理歌曲 '{song_data.get('title')}' 時發生錯誤: {e}")
                db.session.rollback()

        if new_songs_count > 0:
            try:
                db.session.commit()
                print_success(f"成功提交 {new_songs_count} 首新歌曲到資料庫！")
            except Exception as e:
                db.session.rollback()
                print_error(f"最終提交資料庫時發生錯誤: {e}")

if __name__ == "__main__":
    print_info("檢查系統是否支援 IPv6...")
    IPv6_Support = Has_IPv6_Addr()

    if IPv6_Support:
        print_info("系統支援 IPv6，開始上傳爬蟲資料...")
        upload_crawled_data()
    else:
        print_error("Supabase Storage 上傳需要 IPv6 支援。")
        print_error("當前系統不支援 IPv6，請檢查網路設定。")
        print_info("可下載WARP 或其他 VPN 軟體來獲得 IPv6 支援。")
        sys.exit(1)
