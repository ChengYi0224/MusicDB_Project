from app import create_app
from flask_migrate import Migrate
from app.utils.network import Check_IPv6_Dialogue
from wsgiserver import WSGIServer

# 程式入口
if __name__ == "__main__":
    app = create_app()
    app.debug = True  # 啟用除錯模式
    #migrate = Migrate(app, db)
    if Check_IPv6_Dialogue():
        HOST = '0.0.0.0'  # 監聽所有可用的網路介面，讓 playit.gg 可以連線
        PORT = 5000       # 您希望 WSGIserver 監聽的埠口

        print(f"啟動 Flask 應用程式，使用 WSGIserver 監聽在 {HOST}:{PORT}")
        server = WSGIServer(app, host=HOST, port=PORT)
        try:
            print("(按下 Ctrl+C 來停止伺服器)")
            server.start() # 啟動伺服器
        except KeyboardInterrupt:
            server.stop()  # 停止伺服器
            print("\nWSGIserver 已停止。")
        
    