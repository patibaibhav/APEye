"""Tests for LocalStorage and S3Storage integrations (Owner: Anvi)."""

import hashlib

import boto3
import pytest
from moto import mock_aws

from app.core.errors import StorageDisabledError, StorageUnavailableError
from app.integrations.storage import (
    LocalStorage,
    S3Storage,
    get_storage,
)


def test_local_storage_lifecycle(tmp_path):
    storage = LocalStorage(base_dir=str(tmp_path))
    test_key = "dev/reports/2026/01/test.txt"
    test_data = b"Hello Local Storage"

    assert storage.exists(test_key) is False

    info = storage.upload_bytes(test_key, test_data, "text/plain")
    assert info.object_key == test_key
    assert info.size_bytes == len(test_data)
    assert info.sha256 == hashlib.sha256(test_data).hexdigest()
    assert info.backend == "local"

    assert storage.exists(test_key) is True
    read_data = storage.get_bytes(test_key)
    assert read_data == test_data

    presigned = storage.presign_download(test_key)
    assert f"/api/reports/file?key={test_key}" in presigned


def test_local_storage_path_traversal_blocked(tmp_path):
    storage = LocalStorage(base_dir=str(tmp_path))
    with pytest.raises(StorageUnavailableError):
        storage.upload_bytes("../outside.txt", b"malicious", "text/plain")


@mock_aws
def test_s3_storage_lifecycle():
    bucket_name = "test-apeye-bucket"
    region = "us-east-1"

    # Create mock S3 bucket
    s3_client = boto3.client("s3", region_name=region)
    s3_client.create_bucket(Bucket=bucket_name)

    storage = S3Storage(bucket_name=bucket_name, region_name=region)
    test_key = "dev/summary/2026/01/01/report.md"
    test_data = b"# Security Report"

    assert storage.exists(test_key) is False

    info = storage.upload_bytes(
        test_key,
        test_data,
        "text/markdown",
        metadata={"report_type": "SUMMARY"},
    )
    assert info.object_key == test_key
    assert info.size_bytes == len(test_data)
    assert info.sha256 == hashlib.sha256(test_data).hexdigest()
    assert info.backend == "s3"

    assert storage.exists(test_key) is True
    read_data = storage.get_bytes(test_key)
    assert read_data == test_data

    presigned = storage.presign_download(test_key, ttl_seconds=600)
    assert "https://" in presigned
    assert bucket_name in presigned
    assert test_key in presigned


def test_get_storage_factory(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))
    storage = get_storage()
    assert isinstance(storage, LocalStorage)

    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_BUCKET_NAME", "my-bucket")
    storage_s3 = get_storage()
    assert isinstance(storage_s3, S3Storage)

    monkeypatch.setenv("STORAGE_BACKEND", "unsupported_storage")
    with pytest.raises(StorageDisabledError):
        get_storage()
