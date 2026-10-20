# CloudWatch Contract (frozen)

Owner: Anvi. `configure_cloudwatch_logging(settings)` attaches watchtower only when enabled; `get_ops_logger()` returns `app.ops`; `emit_metric(name,value=1.0,unit="Count")` buffers; `flush_metrics()` runs at shutdown. JSON Lines events contain `ts,level,event,request_id` when available plus safe fields. Stream: `{prefix}-{hostname}-{date}` in `CW_LOG_GROUP`.

Events: lifecycle; login outcome (username/IP only); alert created/updated/auto-closed; ingestion/detection errors; report archive outcome; export row count; sanitized unhandled exceptions. Metrics namespace `ApiSecurityMonitor`: `AlertsCreated`, `RequestLogWriteFailures`, `DetectionErrors`, `ReportUploadsFailed`. Never send bodies, headers, tokens, passwords, secrets, or request-log contents. Outages never break the app: emit local stderr note and drop bounded buffered metrics.
