from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # เพิ่มช่องเก็บรหัสผ่าน

    # OOP Relationship: User 1 คน มีหลาย DiaryEntry
    entries = relationship("DiaryEntry", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String, default="Neutral")
    energy_level = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # FK เชื่อมไปยัง User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # OOP Relationship
    owner = relationship("User", back_populates="entries")

    def get_word_count(self):
        return len(self.content.split()) if self.content else 0