"""api v2: directory batches on pipeline runs + standalone agent jobs

Revision ID: api_v2_batch_agent_jobs_20261124
Revises: source_language_20260803
Create Date: 2026-11-24
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "api_v2_batch_agent_jobs_20261124"
down_revision: Union[str, None] = "source_language_20260803"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add directory-batch columns and the standalone agent job queue."""
    op.add_column(
        "pipeline_run_states",
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "pipeline_run_states",
        sa.Column("source_directory", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "pipeline_run_states",
        sa.Column("relative_path", sa.String(length=1024), nullable=True),
    )
    op.create_index("ix_pipeline_run_states_batch_id", "pipeline_run_states", ["batch_id"])

    op.create_table(
        "agent_jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("request_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_kind", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("worker_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.user_id"],
            name=op.f("fk_agent_jobs_owner_user_id_users"),
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ck_agent_jobs_status",
        ),
    )
    op.create_index("ix_agent_jobs_status_created", "agent_jobs", ["status", "created_at"])
    op.create_index("ix_agent_jobs_agent_status", "agent_jobs", ["agent", "status"])
    op.create_index("ix_agent_jobs_owner_status", "agent_jobs", ["owner_user_id", "status", "created_at"])


def downgrade() -> None:
    """Drop the agent job queue and directory-batch columns."""
    op.drop_index("ix_agent_jobs_owner_status", table_name="agent_jobs")
    op.drop_index("ix_agent_jobs_agent_status", table_name="agent_jobs")
    op.drop_index("ix_agent_jobs_status_created", table_name="agent_jobs")
    op.drop_table("agent_jobs")
    op.drop_index("ix_pipeline_run_states_batch_id", table_name="pipeline_run_states")
    op.drop_column("pipeline_run_states", "relative_path")
    op.drop_column("pipeline_run_states", "source_directory")
    op.drop_column("pipeline_run_states", "batch_id")
