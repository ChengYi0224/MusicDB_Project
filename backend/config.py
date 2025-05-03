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
                                                                              
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
