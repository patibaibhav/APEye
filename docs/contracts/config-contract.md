# Configuration Contract (frozen)

Owner: Baibhav; each setting is declared in its owner’s settings module. Inputs are environment variables only. `.env` is never committed; examples contain placeholders only. Inputs with offsets are converted to UTC; naive timestamps are rejected.

| Group | Variables | Defaults / contract | Owner |
|---|---|---|---|
| Core | `APP_ENV`, `LOG_LEVEL`, `TRUSTED_PROXY_COUNT`, `ENABLE_SANDBOX`, `STATIC_DIR` | local/test/aws; INFO; 0 locally and 1 behind nginx; sandbox true local/demo; `app/static` | Baibhav |
| Detection | `DETECTION_IGNORE_IPS`, `DET_LOGIN_PATH`, `DET_BRUTE_FORCE_THRESHOLD`, `DET_BRUTE_FORCE_WINDOW_SECONDS`, `DET_RATE_THRESHOLD`, `DET_RATE_WINDOW_SECONDS`, `DET_UNAUTH_THRESHOLD`, `DET_UNAUTH_WINDOW_SECONDS`, `DET_RECON_MIN_DISTINCT`, `DET_RECON_MIN_REQUESTS`, `DET_RECON_MIN_ERROR_RATIO`, `DET_RECON_WINDOW_SECONDS`, `DET_RECON_SENSITIVE_PATTERNS`, `DET_ALERT_COOLDOWN_SECONDS` | empty; `/api/auth/login`; 10/300; 100/60; 15/600; 15/20/0.5/120/default sensitive list; cooldown 600 | Baibhav |
| Database/auth | `DATABASE_URL`, `DB_POOL_SIZE`, `JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` | PostgreSQL URL; 5; secret ≥32 random chars; 30; admin values only for creation, never stored | Anvi |
| Reporting/storage | `EXPORT_MAX_ROWS`, `STORAGE_BACKEND`, `LOCAL_STORAGE_DIR`, `S3_BUCKET_NAME`, `S3_KEY_PREFIX`, `PRESIGNED_URL_TTL_SECONDS` | 100000; local/s3 default local; `./.local_storage`; private bucket/prefix; 300 | Anvi |
| AWS/CW | `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `CLOUDWATCH_ENABLED`, `CW_LOG_GROUP`, `CW_LOG_STREAM_PREFIX`, `CW_METRICS_NAMESPACE`, `CW_METRICS_FLUSH_SECONDS` | one region; runtime standard credential chain; false locally; group/prefix; `ApiSecurityMonitor`; 60 | Anvi (Baibhav sets deploy credentials) |
| Frontend | `VITE_API_BASE_URL`, `VITE_USE_MOCKS` | `/api`; false | Lava |

Sensitive variables are supplied only as deployment environment properties, are not documented with real values, and must not be logged. Invalid configuration fails startup clearly; cloud integration outages do not fail application requests.
