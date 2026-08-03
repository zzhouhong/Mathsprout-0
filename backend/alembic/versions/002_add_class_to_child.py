"""Add class_name field to children table.

Revision ID: 002
Revises: 001
Create Date: 2026-06-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("children", sa.Column("class_name", sa.String(50), nullable=True))
    op.create_index("ix_children_class_name", "children", ["class_name"])


def downgrade() -> None:
    op.drop_index("ix_children_class_name", table_name="children")
    op.drop_column("children", "class_name")
