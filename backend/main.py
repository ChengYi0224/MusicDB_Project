from app import create_app#, db
from flask_migrate import Migrate
from app.utils import Has_IPv6_Addr

# 程式入口
if __name__ == "__main__":
    app = create_app()
    #migrate = Migrate(app, db)
    if not Has_IPv6_Addr():
        print("本機不支援 IPv6，強制啟動將無法連線資料庫。")
        print("是否強制啟動？(y/n): ", end="")
        force = input().strip().lower() == 'y'
        if not force:
            exit(1)
    
    app.run(debug=True)
    