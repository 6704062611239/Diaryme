from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# สร้างไฟล์ฐานข้อมูลชื่อ diaryme.db ในโฟลเดอร์โปรเจกต์
SQLALCHEMY_DATABASE_URL = "sqlite:///./diaryme.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # จำเป็นสำหรับ SQLite ใน FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency สำหรับดึง Database Session ในแต่ละ Request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()