from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False, default="teacher")
    wechat_openid = Column(String(64), unique=True, nullable=True)
    wechat_unionid = Column(String(64), unique=True, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    school = relationship("School", back_populates="users")
