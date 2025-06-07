# backend/scripts/supabase_handler.py

import os
from supabase import create_client, Client
from app.models import User
from app.models.user import enumRole
from app.extensions import db

# 為了方便呼叫，我們從 crawlers 匯入日誌函式
# 您的 __init__.py 設定讓這件事變得很簡單
from crawler.crawlers import print_info, print_success, print_error, print_warning

def initialize_supabase_client(app):
    """根據 Flask app 的設定來初始化並回傳 Supabase client"""
    supabase_url = app.config.get("SUPABASE_URL")
    supabase_key = app.config.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print_error("Supabase URL 或 Key 未在 Flask config 中設定。")
        return None
    
    print_info("Supabase client 初始化成功。")
    return create_client(supabase_url, supabase_key)

def find_or_create_artist(artist_name: str) -> User:
    """
    根據演出者名稱查詢或建立使用者。
    如果使用者不存在，會建立一個角色為 'artist' 的新使用者。
    """
    if not artist_name:
        print_warning("缺少演出者名稱，無法查詢或建立使用者。")
        return None

    user = User.query.filter_by(username=artist_name).first()
    if user:
        # print_debug(f"找到已存在的演出者: {artist_name} (ID: {user.user_id})")
        return user
    else:
        print_info(f"演出者 '{artist_name}' 不存在，正在建立新使用者...")
        try:
            new_user = User(
                username=artist_name,
                email=None,  # 您的模型允許 email 為空
                role=enumRole.artist # 明確指定角色為演出者
            )
            db.session.add(new_user)
            db.session.flush() # flush 以便立即獲取 user.user_id
            print_success(f"成功建立新演出者: {artist_name} (ID: {new_user.user_id})")
            return new_user
        except Exception as e:
            print_error(f"建立新演出者 '{artist_name}' 時發生錯誤: {e}")
            db.session.rollback()
            return None

def upload_file_to_storage(client: Client, local_path: str, storage_path: str) -> str:
    """
    上傳本地檔案到 Supabase Storage 並回傳公開 URL。
    """
    BUCKET_NAME = "song-files" # 請確保您已在 Supabase 後台建立這個儲存桶

    if not local_path or not os.path.exists(local_path):
        print_warning(f"本地檔案不存在，無法上傳: {local_path}")
        return None
    
    public_url = None
    try:
        print_info(f"正在上傳 '{os.path.basename(local_path)}' 到 Storage...")
        with open(local_path, 'rb') as f:
            # upsert=true: 如果檔案已存在，會直接覆蓋，避免因重複上傳而報錯
            client.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=f,
                file_options={"content-type": "video/mp2t", "upsert": "true"}
            )
        
        public_url = client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        print_success("檔案上傳成功。")
    except Exception as e:
        print_error(f"上傳檔案到 Supabase Storage 時發生錯誤: {e}")

    return public_url

def cleanup_local_file(local_path: str):
    """刪除本地的暫存檔案"""
    if local_path and os.path.exists(local_path):
        try:
            os.remove(local_path)
            # print_debug(f"成功清理本地檔案: {local_path}")
        except OSError as e:
            print_warning(f"清理本地檔案時出錯: {e}")