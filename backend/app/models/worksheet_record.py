"""操作单生成记录：每次生成的操作单留存，供历史查看/他人使用/难度推进。"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class WorksheetRecord(Base):
    __tablename__ = "worksheet_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    theme = Column(String(50), nullable=False, index=True)       # 能力主题 key（count/sort/...）
    difficulty = Column(Integer, nullable=False, default=1)      # 难度阶梯 1/2/3
    age_group = Column(String(20), nullable=True)                # small/middle/large
    child_name = Column(String(50), nullable=True)
    story_title = Column(String(120), nullable=True)
    generation_mode = Column(String(20), nullable=True)          # ai/template/fallback
    markdown = Column(Text, nullable=True)                       # 操作单 markdown（含图形符号）
    pdf_base64 = Column(Text, nullable=True)                     # PDF base64（可导出）
    activity_theme = Column(String(300), nullable=True)          # 教师填的活动情境
    created_at = Column(DateTime, server_default=func.now())
