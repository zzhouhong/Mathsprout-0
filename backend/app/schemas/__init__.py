from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enums ───────────────────────────────────────────────────────────

class AgeGroupEnum(str, Enum):
    SMALL = "small"
    MIDDLE = "middle"
    LARGE = "large"


class UploadMethodEnum(str, Enum):
    CAMERA = "camera"
    FILE = "file"
    SCAN = "scan"


class CompletionContextEnum(str, Enum):
    INDEPENDENT = "independent"
    PROMPTED = "prompted"
    ASSISTED = "assisted"


class ReportTypeEnum(str, Enum):
    TEACHER = "teacher"
    PARENT = "parent"


class LevelEnum(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class ProblemTypeEnum(str, Enum):
    COUNTING = "counting"
    ADD_10 = "add_10"
    SUB_10 = "sub_10"
    NUMBER_COMPOSITION = "number_composition"
    SHAPE_ID = "shape_id"
    SPATIAL = "spatial"
    PATTERN_NEXT = "pattern_next"
    CLASSIFY = "classify"
    COMPARE = "compare"
    SORT = "sort"


class HandwritingQualityEnum(str, Enum):
    CLEAR = "clear"
    MESSY = "messy"
    ILLEGIBLE = "illegible"
    MIRRORED = "mirrored"


class ErasurePatternEnum(str, Enum):
    NONE = "none"
    SELF_CORRECT = "self_correct"
    PERSISTENT_ERROR = "persistent_error"


class AttentionIndicatorEnum(str, Enum):
    COMPLETED_ALL = "completed_all"
    SKIPPED = "skipped"
    RUSHED = "rushed"
    CAREFUL = "careful"


class WorksheetStatusEnum(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    ERROR = "error"


# ─── Request Schemas ─────────────────────────────────────────────────

class ChildCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="幼儿姓名")
    age_group: AgeGroupEnum
    class_name: Optional[str] = Field(None, max_length=50, description="班级名称")
    birth_date: Optional[datetime] = None
    notes: Optional[str] = None


class ChildResponse(BaseModel):
    id: int
    name: str
    age_group: AgeGroupEnum
    class_name: Optional[str] = None
    birth_date: Optional[datetime] = None
    parent_access_code: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorksheetUploadResponse(BaseModel):
    id: int
    child_id: int
    file_path: str
    original_filename: Optional[str] = None
    status: str
    upload_method: UploadMethodEnum
    created_at: datetime


class AnalyzeRequest(BaseModel):
    child_id: Optional[int] = None
    child_name: Optional[str] = None
    age_group: AgeGroupEnum
    file_path: Optional[str] = None
    completion_context: Optional[CompletionContextEnum] = None
    teacher_notes: Optional[str] = None


# ─── Vision Recognition Schemas ──────────────────────────────────────

class ProblemRecognition(BaseModel):
    id: str
    type: ProblemTypeEnum
    child_answer: Optional[str] = None
    correct_answer: str
    is_correct: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    handwriting_quality: HandwritingQualityEnum
    has_erasure: bool = False
    erasure_pattern: ErasurePatternEnum = ErasurePatternEnum.NONE
    strategy_indicators: Optional[str] = None


class WorksheetObservation(BaseModel):
    number_formation_issues: List[str] = Field(default_factory=list)
    attention_indicators: AttentionIndicatorEnum
    task_completion_context: CompletionContextEnum
    overall_pck_notes: Optional[str] = None


class DimensionScoresPreliminary(BaseModel):
    counting: Optional[dict] = None
    addition_subtraction: Optional[dict] = None
    shapes_space: Optional[dict] = None
    patterns: Optional[dict] = None


class VisionRecognitionResponse(BaseModel):
    worksheet_type: str
    age_group_hint: Optional[str] = None
    problems: List[ProblemRecognition]
    observations: WorksheetObservation
    dimension_scores_preliminary: Optional[DimensionScoresPreliminary] = None


# ─── Assessment Schemas ──────────────────────────────────────────────

class SubSkillScore(BaseModel):
    name: str
    score: float
    max_score: float


class DimensionAssessment(BaseModel):
    dimension: str
    display_name: str
    score: float  # 0-100
    level: LevelEnum
    level_name: str
    level_emoji: str
    pck_stage: str
    sub_skills: List[SubSkillScore]
    error_patterns: List[str] = Field(default_factory=list)
    age_benchmark_comparison: str
    recommendations: str


class AnalysisResultResponse(BaseModel):
    worksheet_id: int
    child_name: str
    age_group: AgeGroupEnum
    assessment: List[DimensionAssessment]
    observations: WorksheetObservation
    overall_summary: str


# ─── Report Schemas ──────────────────────────────────────────────────

class TeacherReportData(BaseModel):
    child_name: str
    age_group: str
    generated_at: str
    dimensions: List[DimensionAssessment]
    radar_chart_data: dict
    pck_analysis: str
    typical_errors_diagnosis: List[str]
    teaching_suggestions: dict
    longitudinal_trend: Optional[dict] = None
    class_distribution: Optional[dict] = None
    teaching_reflection_questions: List[str]


class ParentReportData(BaseModel):
    child_name: str
    age_group: str
    generated_at: str
    overall_summary: str
    strengths: List[dict]   # [{"area": "数数", "description": "宝宝已经能..."}]
    growing_areas: List[dict]  # [{"area": "左右区分", "description": "正在学习..."}]
    family_activities: List[dict]  # [{"title": "数筷子游戏", "materials": "...", "steps": "..."}]
    learning_quality_notes: str
    parent_tips: str


class ReportResponse(BaseModel):
    id: int
    child_id: int
    report_type: ReportTypeEnum
    content: dict
    generated_at: datetime


# ─── Progress Streaming ──────────────────────────────────────────────

class ProgressEvent(BaseModel):
    step: str  # preprocessing, recognizing, assessing, generating_report, complete, error
    status: str  # pending, in_progress, completed, error
    message: str
    progress_pct: float = 0.0
    data: Optional[dict] = None
