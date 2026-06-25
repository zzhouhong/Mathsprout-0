from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, Enum as SAEnum
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import ReportTypeEnum


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    worksheet_id = Column(Integer, ForeignKey("worksheets.id"), nullable=True)
    report_type = Column(SAEnum(ReportTypeEnum), nullable=False)
    content_json = Column(JSON, nullable=False)
    teaching_reflections = Column(Text, nullable=True)
    family_activities = Column(Text, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())

    child = relationship("Child", back_populates="reports")


class AIRequestLog(Base):
    __tablename__ = "ai_request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worksheet_id = Column(Integer, ForeignKey("worksheets.id"), nullable=True)
    model_used = Column(String(100), nullable=False)
    prompt_version = Column(String(50), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    caching_hit = Column(Boolean, default=False)
    cost = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
