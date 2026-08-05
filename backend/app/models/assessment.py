from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Enum as SAEnum
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import LevelEnum, enum_values_callable


class AbilityAssessment(Base):
    __tablename__ = "ability_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    dimension = Column(String(50), nullable=False)
    sub_skill = Column(String(100), nullable=True)
    score = Column(Float, nullable=False)
    level = Column(
        SAEnum(LevelEnum, values_callable=enum_values_callable),
        nullable=False,
    )
    pck_stage = Column(String(50), nullable=True)
    error_patterns = Column(JSON, nullable=True)
    age_benchmark_comparison = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    assessed_at = Column(DateTime, server_default=func.now())

    child = relationship("Child", back_populates="ability_assessments")
