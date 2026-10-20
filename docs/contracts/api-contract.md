# API Contract (frozen)

Owner: Baibhav. Base path: `/api`; JSON UTF-8; `Authorization: Bearer <jwt>`.

All timestamps are ISO-8601 UTC with `Z`. `from` is inclusive, `to` exclusive; both require an offset/Z, default to last 24 hours, maximum span 31 days. Pagination is `page` (1-based, default 1) and `page_size` (1–100, default 25), returning `{items,page,page_size,total_items,total_pages}`.

Every non-2xx response is `{ "error": { "code", "message", "details", "request_id" } }`; never expose stack traces. Codes: `UNAUTHENTICATED`, `TOKEN_EXPIRED`, `TOKEN_INVALID`, `INVALID_CREDENTIALS`, `FORBIDDEN`, `NOT_FOUND`, `ALERT_NOT_FOUND`, `VALIDATION_ERROR`, `INVALID_TRANSITION`, `USERNAME_TAKEN`, `EXPORT_TOO_LARGE`, `STORAGE_DISABLED`, `STORAGE_UNAVAILABLE`, `INTERNAL_ERROR`.

## Endpoints

| Method/path | Access | Request | Success |
|---|---|---|---|
| POST `/auth/login` | public | `{username,password}` | 200 `{access_token,token_type:"bearer",expires_at,user:{id,username,role}}` |
| POST `/auth/logout` | ANY | — | 204 |
| GET `/auth/me` | ANY | — | 200 user |
| GET `/users` | ADMIN | pagination | 200 page of users |
| POST `/users` | ADMIN | username, password min 12, role | 201 user |
| PATCH `/users/{id}` | ADMIN | `is_active?`, `role?` | 200 user; self-deactivation forbidden |
| GET `/dashboard/summary` | ANY | from,to | window, request totals, alert totals, distinct suspicious IPs |
| GET `/dashboard/traffic` | ANY | from,to,interval | `{interval,points:[{bucket_start,total,successful,failed}]}` zero-filled |
| GET `/dashboard/status-distribution` | ANY | from,to | `{classes:[{status_class,count}],codes:[{status_code,count}]}` |
| GET `/dashboard/top-endpoints` | ANY | from,to,limit 1–20 | `{items:[{endpoint,request_count,error_count}]}` |
| GET `/dashboard/response-times` | ANY | from,to,interval | `{interval,points:[{bucket_start,avg_ms,p95_ms,max_ms}]}` |
| GET `/dashboard/alert-severity` | ANY | from,to | `{items:[{severity,count}]}`; always LOW/MEDIUM/HIGH |
| GET `/logs`, `/logs/{id}` | ANY | filters / — | page of logs / log; see filters below |
| GET `/alerts`, `/alerts/{id}` | ANY | filters / — | page of alerts / alert detail |
| PATCH `/alerts/{id}/status` | ANY | `{status}` | 200 alert; 409 invalid transition |
| POST `/alerts/{id}/notes` | ANY | `{note}` 1–2000 chars | 201 note |
| GET `/suspicious-ips`, `/suspicious-ips/{ip}` | ANY | filters / — | page / summary plus alerts |
| PATCH `/suspicious-ips/{ip}/investigation` | ANY | `{status,note?}` | 200 summary |
| GET `/exports/logs.csv`, `/exports/alerts.csv` | ANY | matching filters; no pagination | `text/csv`; 413 on cap |
| GET `/reports/summary` | ANY | from,to | security summary |
| POST `/reports/archive` | ADMIN | report_type, from, to, filters? | 201 archive |
| GET `/reports` | ANY | pagination | 200 archive page |
| GET `/reports/{id}/download` | ANY | — | `{url,expires_at}` |
| GET `/health` | public | — | `{status:"ok",database:"ok",version,time}`; 503 DB error |
| GET `/sandbox/ping`, `/protected`, `/admin-only` | public, ANY, ADMIN | — | `{ok:true}` when sandbox enabled |

User fields: `id, username, role, is_active, created_at, last_login_at`. Log fields: `id, request_id, occurred_at, source_ip, path, method, status_code, response_time_ms, auth_outcome, user_id`. Alert list: `id,category,severity,status,source_ip,endpoints,request_count,window_seconds,event_count,first_detected_at,last_detected_at`; detail adds `user_id,threshold,resolved_at,evidence,notes`.

Logs filters combine with AND: exact validated `source_ip`; literal case-sensitive path-prefix `endpoint` (escape LIKE wildcards); exact upper-case method; status 100–599 or `status_class` 2xx–5xx; sort `occurred_at DESC,id DESC`. Alert dates filter `first_detected_at`. An IP appears with an alert in range. Status transitions: ACTIVE→INVESTIGATING/RESOLVED, INVESTIGATING→ACTIVE/RESOLVED, RESOLVED→ACTIVE.

Owners: Anvi owns auth/users/dashboard/logs/exports/reports; Baibhav owns alerts/suspicious IPs/health/sandbox. Frontend client names follow the blueprint table.
