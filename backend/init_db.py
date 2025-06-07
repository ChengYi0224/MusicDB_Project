import os
from app import create_app
from app.extensions import db
from supabase import create_client, Client # 匯入 Supabase Client
from app.utils.network import Check_IPv6_Dialogue

app = create_app()

def clear_supabase_bucket(url: str, key: str, bucket_name: str):
    """連接到 Supabase 並清空指定的 Bucket。"""
    if not all([url, key, bucket_name]):
        print("\n⚠️  Supabase 設定不完整 (URL, KEY, 或 BUCKET_NAME 缺少)，跳過清空 Bucket。")
        return

    try:
        print(f"\n準備清空 Supabase Bucket: '{bucket_name}'...")
        # 使用 URL 和 service_role_key 初始化 Supabase client
        supabase: Client = create_client(url, key)
        
        # 1. 列出 Bucket 中的所有檔案
        files_to_delete = supabase.storage.from_(bucket_name).list()
        
        if not files_to_delete:
            print(f"✅ Bucket '{bucket_name}' 本身就是空的，無需操作。")
            return
            
        # 2. 取得檔案名稱列表
        file_names = [file['name'] for file in files_to_delete]
        
        # 3. 執行刪除
        print(f"正在刪除 Bucket '{bucket_name}' 中的 {len(file_names)} 個檔案...")
        supabase.storage.from_(bucket_name).remove(file_names)
        
        print(f"✅ Bucket '{bucket_name}' 已成功清空！")

    except Exception as e:
        print(f"❌ 清空 Supabase Bucket 時發生錯誤: {e}")
        print("   請檢查您的 SUPABASE_URL、SUPABASE_KEY (必須是 service_role) 和 BUCKET_NAME 是否正確。")


def initialize_database():
    with app.app_context():
        # 從 Flask app 設定中讀取 Supabase 的設定
        supabase_url = app.config.get('SUPABASE_URL')
        supabase_key = app.config.get('SUPABASE_KEY') # 應使用 service_role key
        bucket_name = 'song-files'

        print("\n資料庫與儲存空間初始化選項：")
        print("1. 僅建立尚不存在的資料表 (安全，不影響現有資料)")
        print("2. 刪除所有資料表並清空對應的 Bucket (警告：將清除所有資料！)")
        print("3. 取消操作")

        choice = input("請輸入您的選擇 (1-3): ")

        if choice == '1':
            print("\n正在建立尚不存在的資料表...")
            db.create_all()
            print("✅ 資料表建立完成 (或已存在)！")
        
        elif choice == '2':
            confirm_drop = input("\n⚠️ 警告：這會刪除所有資料庫表格並清空 Supabase Bucket！\n"
                                 "確定要繼續嗎？ (輸入 'y' 以確認): ")
            if confirm_drop.lower() == 'y':
                
                # 步驟 1: 刪除資料庫表格
                print("\n正在刪除所有資料表...")
                db.drop_all()
                print("✅ 所有資料表已刪除！")

                # 步驟 2: 清空 Supabase Bucket
                clear_supabase_bucket(supabase_url, supabase_key, bucket_name)
                
                # 步驟 3: 重建資料庫表格
                print("\n正在重新建立所有資料表...")
                db.create_all()
                print("✅ 資料表重新建立完成！")
            else:
                print("\n操作已取消。")
        
        elif choice == '3':
            print("\n操作已取消。")
        
        else:
            print("\n無效的選擇。")

if __name__ == '__main__':
    if Check_IPv6_Dialogue():
        initialize_database()