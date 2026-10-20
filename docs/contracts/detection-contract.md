# Detection Contract (frozen)

Owner: Baibhav. Shared enums: `ThreatCategory = BRUTE_FORCE | EXCESSIVE_REQUESTS | RECONNAISSANCE | UNAUTHORIZED_ACCESS`; `Severity = LOW | MEDIUM | HIGH`; `AlertStatus = ACTIVE | INVESTIGATING | RESOLVED`; `AuthOutcome = NONE | AUTHENTICATED | LOGIN_SUCCESS | LOGIN_FAILED | TOKEN_INVALID | TOKEN_EXPIRED | FORBIDDEN`.

`RequestEvent`: `request_id`, UTC `occurred_at`, `source_ip`, `path`, `normalized_path`, `method`, `status_code`, non-negative `response_time_ms`, `auth_outcome`, nullable `user_id`.

`DetectionResult`: category, severity, source_ip, nullable user_id, up-to-10 endpoints, request_count, window_seconds, threshold, JSON-serializable evidence, dedup_key, and detected_at (event time). `AlertOutcome`: `action` (`created|updated|auto_closed_and_created|suppressed`) and alert_id.

`WindowCounter` windows are half-open `(event.occurred_at - W, event.occurred_at]`; its methods are `count_requests`, `count_by_status`, `count_login_failures`, `has_login_success`, and `endpoint_profile`. Anvi implements it in `db/repositories/window_repository.py`; rules must not import SQLAlchemy, FastAPI, or boto3.

Rules: brute force = POST login 401s in 300s >10 (`BRUTE_FORCE:IP`); rate = requests/IP in 60s >100 (`EXCESSIVE_REQUESTS:IP`); unauthorized = non-login 401/403 in 600s >15 (`UNAUTHORIZED_ACCESS:IP` or `:user:ID`); reconnaissance = 4xx event and, in 120s, distinct normalized paths ≥15, total ≥20 and 4xx ratio ≥0.5 (`RECONNAISSANCE:IP`). All defaults are environment configurable. Threshold means strictly greater except reconnaissance minimums. Evidence is the blueprint-specified counts/windows/paths/patterns.

`severity_from_ratio(count, threshold)`: <1.5 LOW, 1.5–<3 MEDIUM, ≥3 HIGH. Brute force bumps on subsequent success; reconnaissance bumps for ≥3 sensitive patterns. Engine order: brute force, rate, unauthorized, reconnaissance. Rule failures are isolated and logged; no failure changes the HTTP response.

`process_results(session, results, cooldown_seconds=...)` calls `find_open_by_dedup_key`, `create_alert`, `touch_alert`, `set_status`, `add_note`. Open alerts are ACTIVE/INVESTIGATING. ACTIVE inside cooldown updates; stale ACTIVE auto-closes with system note then creates; INVESTIGATING is never auto-closed. Partial unique conflict re-reads and updates once; severity never lowers. A detection/DB failure rolls back only alert work; the persisted request remains.
