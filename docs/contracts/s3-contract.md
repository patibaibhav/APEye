# Object Storage / S3 Contract (frozen)

Owner: Anvi. `ObjectInfo`: `object_key,size_bytes,sha256,content_type,backend`. `ObjectStorage`: `upload_bytes(key,data,content_type,metadata?)`, `get_bytes(key)`, `presign_download(key,ttl_seconds?)`, `exists(key)`. `get_storage` selects S3 or local. Errors: `StorageUnavailableError`, `StorageDisabledError`.

Keys are `{prefix}/{report_type}/{YYYY}/{MM}/{DD}/{report_type}-{YYYYMMDDTHHMMSSZ}-{8-char-uuid}.{csv|csv.gz|md}`; never include user input. Metadata is report-type, creator ID, range start/end and SHA-256—never log content. Bucket is private, never public ACL, default server-side encryption. Upload errors map to `STORAGE_UNAVAILABLE` (503), write no archive row, and receive no silent retries beyond SDK defaults. Download checks authorization and returns a presigned URL (300s default); local storage returns an authenticated streaming route. Archives: logs gzip CSV; alerts CSV and summary Markdown plain.
