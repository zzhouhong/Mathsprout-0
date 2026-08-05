from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import AgeGroupEnum, enum_values_callable


class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    age_group = Column(
        SAEnum(AgeGroupEnum, values_callable=enum_values_callable),
        nullable=False,
    )
    class_name = Column(String(50), nullable=True, index=True)
    birth_date = Column(DateTime, nullable=True)
    parent_access_code = Column(String(16), unique=True, nullable=False)
    notes = Column(Text, nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    school = relationship("School", back_populates="children")
    worksheets = relationship("Worksheet", back_populates="child")
    ability_assessments = relationship("AbilityAssessment", back_populates="child")
    reports = relationship("Report", back_populates="child")
