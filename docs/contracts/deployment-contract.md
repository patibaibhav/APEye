# Deployment Contract (frozen)

Owner: Baibhav. Baibhav receives green `main`, Lava's frontend build handoff, Anvi's S3/CloudWatch handoff, and the configuration registry. Baibhav produces release zip, running EC2 rehearsal then one Elastic Beanstalk single instance, passing smoke test, and signed release checklist. Deployment does not edit Anvi/Lava source files.

Only EC2, Elastic Beanstalk, RDS PostgreSQL, private S3, and CloudWatch are in scope. RDS is private; nginx fronts gunicorn/uvicorn; `TRUSTED_PROXY_COUNT=1` there. Local defaults: `STORAGE_BACKEND=local`, `CLOUDWATCH_ENABLED=false`. All credentials are runtime environment properties, never Git/docs/logs. EC2 rehearsal is terminated before final Beanstalk operation.

Registry: `APP_ENV`, `LOG_LEVEL`, `TRUSTED_PROXY_COUNT`, `ENABLE_SANDBOX`, `STATIC_DIR`, `DETECTION_IGNORE_IPS`, all `DET_*` thresholds/windows/patterns/cooldown, `DATABASE_URL`, `DB_POOL_SIZE`, `JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `EXPORT_MAX_ROWS`, `STORAGE_BACKEND`, `LOCAL_STORAGE_DIR`, `S3_BUCKET_NAME`, `S3_KEY_PREFIX`, `AWS_REGION`, AWS credentials, `PRESIGNED_URL_TTL_SECONDS`, `CLOUDWATCH_ENABLED`, `CW_LOG_GROUP`, `CW_LOG_STREAM_PREFIX`, `CW_METRICS_NAMESPACE`, `CW_METRICS_FLUSH_SECONDS`, `VITE_API_BASE_URL`, `VITE_USE_MOCKS`. Exact defaults and owners are fixed by the blueprint configuration registry.
