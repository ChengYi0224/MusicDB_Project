from database import Base, engine

# import models.user  # 載入所有 ORM 模型，這很重要！
# import models.album
# import models.song
# ... 加上你所有 models

def init_db():
    print("🔧 初始化資料庫中...")
    Base.metadata.create_all(bind=engine)
    print("✅ 資料庫初始化完成！")

if __name__ == "__main__":
    init_db()
