"""Initial schema — creates all core tables.

Revision ID: 001
Revises:
Create Date: 2026-06-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for Mathsprout."""

    # ─── children ──────────────────────────────────────────────────
    op.create_table(
        "children",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column(
            "age_group",
            sa.Enum("small", "middle", "large", name="agegroupenum"),
            nullable=False,
        ),
        sa.Column("birth_date", sa.DateTime(), nullable=True),
        sa.Column(
            "parent_access_code",
            sa.String(16),
            unique=True,
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parent_access_code"),
    )

    # ─── worksheets ────────────────────────────────────────────────
    op.create_table(
        "worksheets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "child_id",
            sa.Integer(),
            sa.ForeignKey("children.id"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "uploaded", "preprocessed", "analyzing", "analyzed", "error",
                name="worksheetstatusenum",
            ),
            server_default="uploaded",
            nullable=False,
        ),
        sa.Column(
            "upload_method",
            sa.Enum("camera", "file", "scan", name="uploadmethodenum"),
            nullable=False,
        ),
        sa.Column(
            "completion_context",
            sa.Enum("independent", "prompted", "assisted", name="completioncontextenum"),
            nullable=True,
        ),
        sa.Column("teacher_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ─── analysis_results ──────────────────────────────────────────
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "worksheet_id",
            sa.Integer(),
            sa.ForeignKey("worksheets.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("raw_response", postgresql.JSONB(), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("token_usage", postgresql.JSONB(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("age_group_anchor", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("worksheet_id"),
    )

    # ─── problem_results ───────────────────────────────────────────
    op.create_table(
        "problem_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "analysis_id",
            sa.Integer(),
            sa.ForeignKey("analysis_results.id"),
            nullable=False,
        ),
        sa.Column("problem_id", sa.String(20), nullable=False),
        sa.Column("problem_type", sa.String(50), nullable=False),
        sa.Column("child_answer", sa.String(50), nullable=True),
        sa.Column("correct_answer", sa.String(50), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("strategy_indicators", sa.String(100), nullable=True),
        sa.Column("erasure_pattern", sa.String(50), nullable=True),
        sa.Column("dimension", sa.String(50), nullable=False),
        sa.Column("pck_stage_hint", sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ─── ability_assessments ───────────────────────────────────────
    op.create_table(
        "ability_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "child_id",
            sa.Integer(),
            sa.ForeignKey("children.id"),
            nullable=False,
        ),
        sa.Column("dimension", sa.String(50), nullable=False),
        sa.Column("sub_skill", sa.String(100), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column(
            "level",
            sa.Enum("L1", "L2", "L3", "L4", name="levelenum"),
            nullable=False,
        ),
        sa.Column("pck_stage", sa.String(50), nullable=True),
        sa.Column("error_patterns", postgresql.JSONB(), nullable=True),
        sa.Column("age_benchmark_comparison", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column(
            "assessed_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ─── reports ───────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "child_id",
            sa.Integer(),
            sa.ForeignKey("children.id"),
            nullable=False,
        ),
        sa.Column(
            "worksheet_id",
            sa.Integer(),
            sa.ForeignKey("worksheets.id"),
            nullable=True,
        ),
        sa.Column(
            "report_type",
            sa.Enum("teacher", "parent", name="reporttypeenum"),
            nullable=False,
        ),
        sa.Column("content_json", postgresql.JSONB(), nullable=False),
        sa.Column("teaching_reflections", sa.Text(), nullable=True),
        sa.Column("family_activities", sa.Text(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ─── ai_request_logs ───────────────────────────────────────────
    op.create_table(
        "ai_request_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "worksheet_id",
            sa.Integer(),
            sa.ForeignKey("worksheets.id"),
            nullable=True,
        ),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("caching_hit", sa.Boolean(), server_default="false"),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ─── Indexes ───────────────────────────────────────────────────
    op.create_index("ix_worksheets_child_id", "worksheets", ["child_id"])
    op.create_index("ix_worksheets_status", "worksheets", ["status"])
    op.create_index("ix_worksheets_created_at", "worksheets", ["created_at"])
    op.create_index(
        "ix_ability_assessments_child_dimension",
        "ability_assessments",
        ["child_id", "dimension"],
    )
    op.create_index(
        "ix_ability_assessments_assessed_at",
        "ability_assessments",
        ["assessed_at"],
    )
    op.create_index("ix_reports_child_id", "reports", ["child_id"])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index("ix_reports_child_id")
    op.drop_index("ix_ability_assessments_assessed_at")
    op.drop_index("ix_ability_assessments_child_dimension")
    op.drop_index("ix_worksheets_created_at")
    op.drop_index("ix_worksheets_status")
    op.drop_index("ix_worksheets_child_id")

    op.drop_table("ai_request_logs")
    op.drop_table("reports")
    op.drop_table("ability_assessments")
    op.drop_table("problem_results")
    op.drop_table("analysis_results")
    op.drop_table("worksheets")
    op.drop_table("children")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS reporttypeenum")
    op.execute("DROP TYPE IF EXISTS levelenum")
    op.execute("DROP TYPE IF EXISTS completioncontextenum")
    op.execute("DROP TYPE IF EXISTS uploadmethodenum")
    op.execute("DROP TYPE IF EXISTS worksheetstatusenum")
    op.execute("DROP TYPE IF EXISTS agegroupenum")
