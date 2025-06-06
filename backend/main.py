from app import create_app
from app.utils import Has_IPv6_Addr

# 程式入口
if __name__ == "__main__":
    if Has_IPv6_Addr():
        app = create_app()

        # 啟動伺服器
        app.run(debug=True)
    else:
        print("您的系統不支援 IPv6，請使用WARP或其他方式啟用 IPv6。")
        exit(1)