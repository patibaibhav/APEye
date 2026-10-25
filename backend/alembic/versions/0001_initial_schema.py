"""Initial schema migration (Owner: Anvi).

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-25 00:00:00.000000

Creates all tables per database-contract.md:
1. users
2. api_request_logs
3. alerts
4. alert_notes
5. ip_investigations
6. report_archives
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('ADMIN', 'ANALYST')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # 2. api_request_logs
    op.create_table(
        "api_request_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_ip", sa.String(length=45), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("normalized_path", sa.String(length=512), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("status_code", sa.SmallInteger(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column("auth_outcome", sa.String(length=30), server_default="NONE", nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("response_time_ms >= 0", name="ck_api_request_logs_response_time_positive"),
        sa.CheckConstraint(
            "auth_outcome IN ('NONE', 'AUTHENTICATED', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'TOKEN_INVALID', 'TOKEN_EXPIRED', 'FORBIDDEN')",
            name="ck_api_request_logs_auth_outcome",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_request_logs_request_id", "api_request_logs", ["request_id"], unique=True)
    op.create_index("ix_api_request_logs_occurred_at", "api_request_logs", ["occurred_at"])
    op.create_index("ix_api_request_logs_source_ip_occurred", "api_request_logs", ["source_ip", "occurred_at"])
    op.create_index("ix_api_request_logs_status_occurred", "api_request_logs", ["status_code", "occurred_at"])
    op.create_index("ix_api_request_logs_norm_path_occurred", "api_request_logs", ["normalized_path", "occurred_at"])
    op.create_index(
        "ix_api_request_logs_user_occurred",
        "api_request_logs",
        ["user_id", "occurred_at"],
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    op.create_index(
        "ix_api_request_logs_path_pattern",
        "api_request_logs",
        ["path"],
        postgresql_ops={"path": "varchar_pattern_ops"},
    )

    # 3. alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ACTIVE", nullable=False),
        sa.Column("source_ip", sa.String(length=45), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("dedup_key", sa.String(length=128), nullable=False),
        sa.Column("endpoints", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("event_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("first_detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "category IN ('BRUTE_FORCE', 'EXCESSIVE_REQUESTS', 'RECONNAISSANCE', 'UNAUTHORIZED_ACCESS')",
            name="ck_alerts_category",
        ),
        sa.CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH')", name="ck_alerts_severity"),
        sa.CheckConstraint("status IN ('ACTIVE', 'INVESTIGATING', 'RESOLVED')", name="ck_alerts_status"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_alerts_dedup_active_investigating",
        "alerts",
        ["dedup_key"],
        unique=True,
        postgresql_where=sa.text("status IN ('ACTIVE', 'INVESTIGATING')"),
    )
    op.create_index("ix_alerts_status_severity_category", "alerts", ["status", "severity", "category"])
    op.create_index("ix_alerts_first_detected_at", "alerts", ["first_detected_at"])
    op.create_index("ix_alerts_source_ip_last_detected", "alerts", ["source_ip", "last_detected_at"])

    # 4. alert_notes
    op.create_table(
        "alert_notes",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("alert_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=True),
        sa.Column("note", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_notes_alert_id_created", "alert_notes", ["alert_id", "created_at"])

    # 5. ip_investigations
    op.create_table(
        "ip_investigations",
        sa.Column("source_ip", sa.String(length=45), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="NEW", nullable=False),
        sa.Column("note", sa.String(length=2000), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('NEW', 'INVESTIGATING', 'RESOLVED')", name="ck_ip_investigations_status"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("source_ip"),
    )

    # 6. report_archives
    op.create_table(
        "report_archives",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("object_key", sa.String(length=512), nullable=False),
        sa.Column("storage_backend", sa.String(length=20), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.CHAR(length=64), nullable=False),
        sa.Column("range_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("range_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "report_type IN ('LOGS_CSV', 'ALERTS_CSV', 'SUMMARY')",
            name="ck_report_archives_report_type",
        ),
        sa.CheckConstraint(
            "storage_backend IN ('s3', 'local')",
            name="ck_report_archives_storage_backend",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_archives_object_key", "report_archives", ["object_key"], unique=True)
    op.create_index("ix_report_archives_created_at", "report_archives", ["created_at"])


def downgrade() -> None:
    op.drop_table("report_archives")
    op.drop_table("ip_investigations")
    op.drop_table("alert_notes")
    op.drop_table("alerts")
    op.drop_table("api_request_logs")
    op.drop_table("users")
