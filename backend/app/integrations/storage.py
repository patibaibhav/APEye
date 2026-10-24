"""Object storage integration supporting Local Storage and AWS S3 (Owner: Anvi).

Follows s3-contract.md:
- ObjectInfo: object_key, size_bytes, sha256, content_type, backend
- ObjectStorage: upload_bytes, get_bytes, presign_download, exists
- Error handling maps AWS/IO failures to StorageUnavailableError / StorageDisabledError
- Never exposes internal filesystem paths as public download URLs
"""

import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.core.errors import StorageDisabledError, StorageUnavailableError


class ObjectInfo(BaseModel):
    object_key: str
    size_bytes: int
    sha256: str
    content_type: str
    backend: str


class ObjectStorage(ABC):
    """Abstract interface for object storage."""

    @abstractmethod
    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> ObjectInfo:
        pass

    @abstractmethod
    def get_bytes(self, key: str) -> bytes:
        pass

    @abstractmethod
    def presign_download(self, key: str, ttl_seconds: int = 300) -> str:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass


class LocalStorage(ObjectStorage):
    """Local filesystem storage backend for development and offline testing."""

    def __init__(self, base_dir: str = "./.local_storage") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        # Prevent directory traversal
        clean_key = os.path.normpath(key).lstrip(os.path.sep)
        target = (self.base_dir / clean_key).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise StorageUnavailableError("Invalid storage key path traversal")
        return target

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> ObjectInfo:
        try:
            target_path = self._resolve_path(key)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(data)

            sha256 = hashlib.sha256(data).hexdigest()
            return ObjectInfo(
                object_key=key,
                size_bytes=len(data),
                sha256=sha256,
                content_type=content_type,
                backend="local",
            )
        except Exception as exc:
            raise StorageUnavailableError(f"Local storage write failed: {exc}") from exc

    def get_bytes(self, key: str) -> bytes:
        try:
            target_path = self._resolve_path(key)
            if not target_path.is_file():
                raise StorageUnavailableError(f"Storage object not found: {key}")
            return target_path.read_bytes()
        except Exception as exc:
            if isinstance(exc, StorageUnavailableError):
                raise
            raise StorageUnavailableError(f"Local storage read failed: {exc}") from exc

    def presign_download(self, key: str, ttl_seconds: int = 300) -> str:
        # For local storage, returns the authenticated internal streaming URL
        # Never expose local filesystem paths!
        return f"/api/reports/file?key={key}"

    def exists(self, key: str) -> bool:
        try:
            return self._resolve_path(key).is_file()
        except Exception:
            return False


class S3Storage(ObjectStorage):
    """AWS S3 private object storage backend."""

    def __init__(
        self,
        bucket_name: str,
        region_name: str = "us-east-1",
    ) -> None:
        self.bucket_name = bucket_name
        self.region_name = region_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "s3",
                region_name=self.region_name,
                config=Config(signature_version="s3v4"),
            )
        return self._client

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> ObjectInfo:
        try:
            client = self._get_client()
            put_args: Dict[str, Any] = {
                "Bucket": self.bucket_name,
                "Key": key,
                "Body": data,
                "ContentType": content_type,
                "ServerSideEncryption": "AES256",
            }
            if metadata:
                put_args["Metadata"] = metadata

            client.put_object(**put_args)

            sha256 = hashlib.sha256(data).hexdigest()
            return ObjectInfo(
                object_key=key,
                size_bytes=len(data),
                sha256=sha256,
                content_type=content_type,
                backend="s3",
            )
        except Exception as exc:
            raise StorageUnavailableError(f"S3 upload failed: {exc}") from exc

    def get_bytes(self, key: str) -> bytes:
        try:
            client = self._get_client()
            resp = client.get_object(Bucket=self.bucket_name, Key=key)
            return resp["Body"].read()
        except Exception as exc:
            raise StorageUnavailableError(f"S3 get_object failed: {exc}") from exc

    def presign_download(self, key: str, ttl_seconds: int = 300) -> str:
        try:
            client = self._get_client()
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=ttl_seconds,
            )
            return url
        except Exception as exc:
            raise StorageUnavailableError(f"Failed to generate S3 presigned URL: {exc}") from exc

    def exists(self, key: str) -> bool:
        try:
            client = self._get_client()
            client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False


def get_storage(storage_backend: Optional[str] = None) -> ObjectStorage:
    """Factory selecting the configured storage backend (local or s3)."""
    backend = storage_backend or os.getenv("STORAGE_BACKEND", "local").lower()

    if backend == "local":
        local_dir = os.getenv("LOCAL_STORAGE_DIR", "./.local_storage")
        return LocalStorage(base_dir=local_dir)
    elif backend == "s3":
        bucket = os.getenv("S3_BUCKET_NAME", "apeye-private-reports-bucket")
        region = os.getenv("AWS_REGION", "us-east-1")
        return S3Storage(bucket_name=bucket, region_name=region)
    else:
        raise StorageDisabledError(f"Storage backend '{backend}' is disabled or unsupported")


def generate_report_object_key(report_type: str, created_at: datetime, extension: str) -> str:
    """Builds contract-compliant object key:

    {prefix}/{report_type_lower}/{YYYY}/{MM}/{DD}/{report_type_lower}-{YYYYMMDDTHHMMSSZ}-{8-char-uuid}.{ext}
    """
    import uuid

    prefix = os.getenv("S3_KEY_PREFIX", "dev").strip("/")
    rt_lower = report_type.lower()
    date_path = created_at.strftime("%Y/%m/%d")
    timestamp_str = created_at.strftime("%Y%m%dT%H%M%SZ")
    unique_suffix = uuid.uuid4().hex[:8]
    ext = extension.lstrip(".")

    return f"{prefix}/{rt_lower}/{date_path}/{rt_lower}-{timestamp_str}-{unique_suffix}.{ext}"
