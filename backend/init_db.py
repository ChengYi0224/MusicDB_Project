from app import create_app
from app.extensions import db

app = create_app()

def initialize_database():
    with app.app_context():
        print("\n資料庫初始化選項：")
        print("1. 僅建立尚不存在的資料表 (安全，不影響現有資料)")
        print("2. 刪除所有現有資料表並重新建立 (警告：將清除所有資料！僅限開發環境使用)")
        print("3. 取消操作")

        choice = input("請輸入您的選擇 (1-3): ")

        if choice == '1':
            print("\n正在建立尚不存在的資料表...")
            db.create_all()
            print("✅ 資料表建立完成 (或已存在)！")
        
        elif choice == '2':
            confirm_drop = input("\n⚠️ 警告：這個操作將會刪除所有資料表及其全部資料！\n"
                                 "這通常只在開發環境中，當您想要一個全新的資料庫結構時使用。\n"
                                 "您確定要繼續嗎？ (輸入 'y' 以確認): ")
            if confirm_drop.lower() == 'y':
                print("\n正在刪除所有資料表...")
                db.drop_all()
                print("✅ 所有資料表已刪除！")
                print("\n正在重新建立所有資料表...")
                db.create_all()
                print("✅ 資料表重新建立完成！")
            else:
                print("\n操作已取消。未對資料庫進行任何更改。")
        
        elif choice == '3':
            print("\n操作已取消。")
        
        else:
            print("\n無效的選擇。請執行腳本並輸入 1、2 或 3。")

if __name__ == '__main__':
    initialize_database()