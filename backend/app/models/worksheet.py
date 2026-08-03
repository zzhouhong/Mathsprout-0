from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, Enum as SAEnum
from sqlalchemy import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import WorksheetStatusEnum, UploadMethodEnum, CompletionContextEnum


class Worksheet(Base):
    __tablename__ = "worksheets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    status = Column(SAEnum(WorksheetStatusEnum), default=WorksheetStatusEnum.UPLOADED)
    upload_method = Column(SAEnum(UploadMethodEnum), nullable=False)
    completion_context = Column(SAEnum(CompletionContextEnum), nullable=True)
    teacher_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    child = relationship("Child", back_populates="worksheets")
    analysis_result = relationship("AnalysisResult", back_populates="worksheet", uselist=False)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worksheet_id = Column(Integer, ForeignKey("worksheets.id"), unique=True, nullable=False)
    raw_response = Column(JSON, nullable=False)
    model_used = Column(String(100), nullable=True)
    token_usage = Column(JSON, nullable=True)
    cost = Column(Float, nullable=True)
    age_group_anchor = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    worksheet = relationship("Worksheet", back_populates="analysis_result")
    problem_results = relationship("ProblemResult", back_populates="analysis_result")


class ProblemResult(Base):
    __tablename__ = "problem_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    problem_id = Column(String(20), nullable=False)
    problem_type = Column(String(50), nullable=False)
    child_answer = Column(String(50), nullable=True)
    correct_answer = Column(String(50), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=True)
    strategy_indicators = Column(String(100), nullable=True)
    erasure_pattern = Column(String(50), nullable=True)
    dimension = Column(String(50), nullable=False)
    pck_stage_hint = Column(String(50), nullable=True)

    analysis_result = relationship("AnalysisResult", back_populates="problem_results")
