from app import create_app

# 程式入口
if __name__ == "__main__":
    app = create_app()

    # 啟動伺服器
    app.run(debug=True)