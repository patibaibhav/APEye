# Database Contract (frozen)

Owner: Anvi. PostgreSQL only: snake_case plural tables, BIGINT identity primary keys, UTC `TIMESTAMPTZ`, VARCHAR plus CHECK enums, explicit FK delete actions. Alembic history is single linear and Anvi-only; `0001_initial_schema.py` creates/downgrades all tables; migrations never run at app start.

| Table | Required columns and constraints | Keys/indexes |
|---|---|---|
| `users` | username VARCHAR(50) unique/non-null; password_hash; role ADMIN/ANALYST; is_active default true; created_at; nullable last_login_at | PK id; unique username |
| `api_request_logs` | request_id VARCHAR(36), occurred_at, source_ip VARCHAR(45), path/normalized_path VARCHAR(512), method VARCHAR(10), status_code SMALLINT, response_time_ms INTEGER ≥0, auth_outcome default NONE, nullable user_id, created_at | unique request_id; FK user SET NULL; indexes occurred_at, (source_ip,occurred_at), (status_code,occurred_at), (normalized_path,occurred_at), partial (user_id,occurred_at), path text_pattern_ops |
| `alerts` | category, severity, status default ACTIVE, source_ip, nullable user_id, dedup_key VARCHAR(128), endpoints JSONB default [], evidence JSONB default {}, request_count/window_seconds/threshold, event_count default 1, first/last_detected_at, nullable resolved_at/updated_by, created/updated_at | user/updated_by FKs SET NULL; partial unique dedup_key where ACTIVE/INVESTIGATING; status/severity/category, first_detected_at, (source_ip,last_detected_at) |
| `alert_notes` | alert_id, nullable author_id (null = system), note VARCHAR(2000), created_at | alert CASCADE; author SET NULL; (alert_id,created_at) |
| `ip_investigations` | source_ip PK, status NEW/INVESTIGATING/RESOLVED default NEW, nullable note, updated_by, updated_at | updated_by SET NULL |
| `report_archives` | report_type LOGS_CSV/ALERTS_CSV/SUMMARY; object_key, storage_backend s3/local, content_type, size_bytes, sha256 CHAR(64), range_start/end, filters JSONB, nullable created_by, created_at | created_by SET NULL; unique object_key; created_at |

Suspicious IPs are a derived alert-grouped view; no IP table or manual blocking schema. All SQL is in repositories; routes/services never write raw SQL.
