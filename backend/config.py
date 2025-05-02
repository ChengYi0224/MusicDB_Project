
class Config:
    SECRET_KEY = "your_secret_key"
    DB_PASSWORD = "MusicDBPassword"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"postgresql://postgres:{DB_PASSWORD}@db.jhdsifyqyxgrioeuloef.supabase.co:5432/postgres"

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
