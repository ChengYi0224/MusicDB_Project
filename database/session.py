from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base

DB_PASSWORD = "MusicDBPassword"
DB_URL = f"postgresql://postgres:{DB_PASSWORD}@db.jhdsifyqyxgrioeuloef.supabase.co:5432/postgres"

engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)