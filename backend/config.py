#config.py
Host = "db.jhdsifyqyxgrioeuloef.supabase.co"
Port = 5432
Database = "postgres"
User = "postgres"

Password = "MusicDBPassword"
# 這是用來連接 PostgreSQL 資料庫的設定檔
# 你可以根據需要修改這些設定

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"postgresql://{User}:{Password}@{Host}:{Port}/{Database}"
    SECRET_KEY = "MusicDB_SECRET_KEY"
    SUPABASE_URL = "https://jhdsifyqyxgrioeuloef.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpoZHNpZnlxeXhncmlvZXVsb2VmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTQ3MTQ4NSwiZXhwIjoyMDYxMDQ3NDg1fQ._1cKXAkU-DivSuw8Hem66DW-A0ValsOR1ucZq-9zX_I"
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }


# =========== 處理crawler輸出檔案的路徑 ==========
import os

# 取得專案根目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Crawler 相關路徑 ---
CRAWLER_DIR = os.path.join(BASE_DIR, 'crawler')

# 爬蟲結果和下載檔案
DOWNLOAD_BASE_DIR = os.path.join(CRAWLER_DIR, 'downloads')
CRAWLER_RESULTS_DIR = os.path.join(CRAWLER_DIR, 'crawled_results')

# 確保這些資料夾存在
os.makedirs(DOWNLOAD_BASE_DIR, exist_ok=True)
os.makedirs(CRAWLER_RESULTS_DIR, exist_ok=True)

# 定義兩個爬蟲各自的輸出檔案路徑
BROWSE_CRAWLER_OUTPUT_FILE = os.path.join(CRAWLER_RESULTS_DIR, 'crawled_from_browse.txt')
PLAYLIST_CRAWLER_OUTPUT_FILE = os.path.join(CRAWLER_RESULTS_DIR, 'crawled_from_playlists.txt')

# ==============================================