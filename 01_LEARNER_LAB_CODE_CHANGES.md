# APEye: Code Changes Required for AWS Academy Learner Lab

Applies to the repo you uploaded (`APEye-dev4.zip`). Do the steps in order, once. Nothing in your project is deleted or renamed. Every edit is additive and keeps local development working exactly as before, because all new behavior is switched on only by environment variables (`CLOUDWATCH_ENABLED=true`, `STORAGE_BACKEND=s3`) that are off locally.

The companion file `02_DEPLOY_LEARNER_LAB_STEP_BY_STEP.md` is the click-by-click deployment guide. Finish this file first.

> Note on wording: Learner Lab makes you pick a pre-made role and instance profile (named `LabRole` and `LabInstanceProfile`) in the console. That wording appears in the deployment guide because the console asks for it. If your team's rules say to keep it out of `AGENTS.md` and the project contracts, keep it out of those files; none of the changes below add it to your code or contracts.

---

## 1. What I checked and what I found

I read your whole repo: backend, deploy files, build script, README, contracts, and frontend config.

**Already compatible with Learner Lab (no change needed):**

- `integrations/storage.py` creates the S3 client with `boto3.client("s3", region_name=...)` and no keys, so boto3 uses the instance profile automatically. Presigned URLs, private objects, and AES256 encryption are already there.
- `core/config.py`, `db/config.py`, and `auth/config.py` read everything from environment variables, which is exactly how Elastic Beanstalk and systemd supply them.
- `static_site.py` serves the React build and falls back to `index.html` for deep links.
- `/api/health` checks the database, so it works as the Beanstalk health check.
- `TRUSTED_PROXY_COUNT=1` is already set in `deploy/eb/.ebextensions/01_options.config`, which is correct behind Beanstalk's nginx.
- Frontend uses relative `/api`, so no frontend code changes are needed.

**Problems that would break or silently fail on AWS (these are what the changes below fix):**

| # | Problem | Effect if not fixed |
|---|---|---|
| P1 | `scripts/build_release.sh` zips `backend/` and `deploy/` as sub-folders. Beanstalk needs `Procfile`, `requirements.txt`, and `app/` at the **root** of the zip. | Beanstalk deployment fails or the app never starts. |
| P2 | `deploy/eb/.platform/nginx/conf.d/proxy.conf` contains a `location / { ... }` block. Beanstalk includes that folder inside nginx's `http {}` block, where `location` is not allowed. | nginx config test fails and the deployment breaks. |
| P3 | The migration command `alembic upgrade head` runs without activating the Beanstalk virtualenv or loading the environment properties. | `alembic: command not found` or no DB URL, so the tables are never created. |
| P4 | `configure_cloudwatch_logging()`, `emit_metric()`, and `flush_metrics()` exist but are **never called** anywhere in the app. | Nothing ever reaches CloudWatch. Your CloudWatch requirement would be empty on AWS. |
| P5 | Logs sent by the CloudWatch handler use the default format, not your JSON format. | Log events are hard to read and search. |
| P6 | `.env.example` and the docs tell you to set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. Learner Lab credentials are temporary (they include a session token and change every session). | S3 and CloudWatch would stop working after the first lab restart. |
| P7 | `build_release.sh` needs `bash` and `zip` and can leak a local `frontend/.env` setting (for example `VITE_USE_MOCKS=true`) into the production build. Windows zip tools also write backslash paths that Linux cannot read. | Broken or mock-data production build, or an unreadable zip. |
| P8 | `create_admin.py` is not in the release zip and `seed_demo_data.py` creates fixed, well-known passwords (`AnalystPass123!`, default `AdminPass123!`). | No way to create the admin on AWS. Seeding a public site with known passwords is unsafe. |

**What I could and could not verify here.** I applied every change below to a copy of your repo. I confirmed that all changed and new Python files compile, and that the new build script produces a correct Elastic Beanstalk zip layout from your repo. I could **not** run your pytest suite (its dependencies were not installable in my environment), and I cannot test against real AWS. So Step 10 asks you to run the tests yourself, and the deployment guide tells you which AWS log files to check if something differs.

---

## 2. Change list at a glance

| Step | File | Action | Fixes |
|---|---|---|---|
| 3 | `scripts/build_release.py` | **new** | P1, P7, P8 |
| 4 | `deploy/eb/eb_migrate.sh` | **new** | P3 |
| 5 | `deploy/eb/.ebextensions/01_options.config` | replace contents | P3, P6 |
| 6 | `deploy/eb/.platform/nginx/conf.d/proxy.conf` | replace contents | P2 |
| 7a | `backend/app/integrations/cloudwatch.py` | edit (replace one function, append two) | P4, P5 |
| 7b | `backend/app/main.py` | edit (3 small edits) | P4 |
| 7c | `backend/app/services/ingestion_service.py` | edit (import + 2 lines) | P4 |
| 7d | `backend/app/services/alert_service.py` | edit (import + 2 lines) | P4 |
| 7e | `backend/app/services/report_service.py` | edit (import + try/except) | P4 |
| 7f | `backend/.env.example` | edit (AWS key lines) | P6 |
| 8 | `backend/tests/integrations/test_cloudwatch_flusher.py` | **new** | covers P4 |
| 9 | `scripts/aws_smoke_test.py` | **new** | verification |

Files you do **not** touch: all frontend files, all other backend files, `scripts/build_release.sh`, `deploy/ec2/setup.sh`, migrations, contracts, `AGENTS.md`.

---

## 3. Step 1: Back up and create a branch

From the repo root:

```bash
git status                       # make sure your work is committed first
git checkout -b learner-lab-deploy
```

No git? Copy the whole folder to `APEye-dev4-backup` first. Rolling back is then `git checkout main` (or deleting the branch), and nothing on `main` changes.

## 4. Step 2: Optional line-ending guard (recommended on Windows)

Create `.gitattributes` in the repo root so shell scripts and Beanstalk config files keep Linux line endings:

```text
*.sh text eol=lf
Procfile text eol=lf
*.config text eol=lf
*.conf text eol=lf
```

(The new build script also converts line endings while zipping, so this is a second safety net.)

---

## 5. Step 3: Add `scripts/build_release.py` (new file)

Cross-platform replacement for the old shell script. The old `build_release.sh` stays in place, unused. It builds the frontend with mock mode forced off, copies it into `backend/app/static`, and writes two zips to `dist/`:

- `dist/apeye-eb.zip` for Elastic Beanstalk (correct root layout; includes `create_admin.py`; excludes tests, `.env`, `seed_demo_data.py`).
- `dist/apeye-ec2.zip` for the optional EC2 rehearsal (keeps the `backend/` and `deploy/ec2/` folders that `setup.sh` expects).

It also checks the Beanstalk zip layout and stops with an error if something required is missing.

```python
#!/usr/bin/env python3
"""Cross-platform release builder for APEye (works on Windows, macOS, Linux).

Produces two zip files in dist/:
  apeye-eb.zip   Elastic Beanstalk bundle (Procfile, requirements.txt, app/ at the zip ROOT)
  apeye-ec2.zip  EC2 rehearsal bundle (backend/ and deploy/ folders, used by deploy/ec2/setup.sh)

The original scripts/build_release.sh is left untouched.

Usage (from the repo root):
  python scripts/build_release.py                 # builds the frontend, then both zips
  python scripts/build_release.py --skip-frontend # reuse the existing backend/app/static
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
STATIC = BACKEND / "app" / "static"
DIST = ROOT / "dist"

SKIP_DIRS = {
    ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".ruff_cache",
    "tests", ".local_storage", "node_modules", ".git",
}
SKIP_FILES = {".env", ".env.local", ".DS_Store", ".gitkeep"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
TEXT_SUFFIXES = {".sh", ".config", ".conf", ".service", ".py", ".txt", ".ini", ".mako"}
TEXT_NAMES = {"Procfile"}


def run(cmd, cwd, env=None):
    print(f"$ {' '.join(cmd)}   (in {cwd})")
    subprocess.run(cmd, cwd=cwd, env=env, check=True, shell=(os.name == "nt"))


def build_frontend() -> None:
    env = dict(os.environ)
    # Process env vars beat frontend/.env files, so a leftover mock setting can never leak in.
    env["VITE_USE_MOCKS"] = "false"
    env["VITE_API_BASE_URL"] = "/api"
    run(["npm", "ci"], FRONTEND, env)
    run(["npm", "run", "build"], FRONTEND, env)
    dist = FRONTEND / "dist"
    if not (dist / "index.html").is_file():
        sys.exit("ERROR: frontend/dist/index.html missing after build")
    STATIC.mkdir(parents=True, exist_ok=True)
    for item in STATIC.iterdir():
        if item.name == ".gitkeep":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    for item in dist.iterdir():
        target = STATIC / item.name
        shutil.copytree(item, target) if item.is_dir() else shutil.copy2(item, target)
    print(f"Frontend copied to {STATIC}")


def iter_files(base: Path):
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if path.name in SKIP_FILES or path.suffix in SKIP_SUFFIXES:
            continue
        yield path, rel


def add(zf: zipfile.ZipFile, path: Path, arcname: str) -> None:
    data = path.read_bytes()
    if path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES:
        data = data.replace(b"\r\n", b"\n")  # Linux hosts need LF line endings
    zf.writestr(arcname.replace("\\", "/"), data)


def build_eb_zip() -> Path:
    out = DIST / "apeye-eb.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, rel in iter_files(BACKEND):          # backend/* -> zip root
            if rel.name == ".env.example":
                continue
            add(zf, path, rel.as_posix())
        eb = ROOT / "deploy" / "eb"                    # Procfile, .ebextensions, .platform, eb_migrate.sh -> root
        for path, rel in iter_files(eb):
            add(zf, path, rel.as_posix())
        add(zf, ROOT / "create_admin.py", "create_admin.py")
    return out


def build_ec2_zip() -> Path:
    out = DIST / "apeye-ec2.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, rel in iter_files(BACKEND):
            if rel.name == ".env.example":
                continue
            add(zf, path, ("backend" / rel).as_posix())
        add(zf, ROOT / "deploy" / "ec2" / "setup.sh", "deploy/ec2/setup.sh")
        add(zf, ROOT / "create_admin.py", "create_admin.py")
    return out


def verify_eb_zip(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
    required = [
        "Procfile", "requirements.txt", "alembic.ini", "eb_migrate.sh", "create_admin.py",
        ".ebextensions/01_options.config", ".platform/nginx/conf.d/proxy.conf",
        "app/main.py", "app/static/index.html", "alembic/versions/0001_initial_schema.py",
    ]
    missing = [r for r in required if r not in names]
    if missing:
        sys.exit(f"ERROR: {path.name} is missing: {missing}")
    if any(n.startswith("backend/") for n in names):
        sys.exit("ERROR: EB zip must not contain a backend/ folder")
    print(f"OK: {path.name} layout verified ({len(names)} files)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build APEye release zips")
    parser.add_argument("--skip-frontend", action="store_true", help="reuse backend/app/static as is")
    args = parser.parse_args()

    if not args.skip_frontend:
        build_frontend()
    if not (STATIC / "index.html").is_file():
        sys.exit("ERROR: backend/app/static/index.html not found (run without --skip-frontend)")

    DIST.mkdir(exist_ok=True)
    eb_zip = build_eb_zip()
    ec2_zip = build_ec2_zip()
    verify_eb_zip(eb_zip)
    for z in (eb_zip, ec2_zip):
        print(f"{z.name}: {z.stat().st_size / 1024 / 1024:.1f} MB")
    print("Done. Upload dist/apeye-eb.zip to Elastic Beanstalk, or dist/apeye-ec2.zip to the EC2 host.")


if __name__ == "__main__":
    main()
```

## 6. Step 4: Add `deploy/eb/eb_migrate.sh` (new file)

Runs the database migration during a Beanstalk deployment, with the virtualenv and environment properties loaded. It is started with `bash eb_migrate.sh`, so no executable permission is required.

```bash
#!/bin/bash
# Runs Alembic migrations during an Elastic Beanstalk deployment (Amazon Linux 2023 Python platform).
# Invoked from .ebextensions/01_options.config with "bash eb_migrate.sh" so no executable bit is needed.
set -e
if [ -f /opt/elasticbeanstalk/deployment/env ]; then
  set -a
  . /opt/elasticbeanstalk/deployment/env
  set +a
fi
VENV_DIR=$(ls -d /var/app/venv/*/ | head -n 1)
. "${VENV_DIR}bin/activate"
cd "$(dirname "$0")"
alembic upgrade head
```

## 7. Step 5: Replace `deploy/eb/.ebextensions/01_options.config`

Replace the whole file with the following. Changes from yours: values are quoted (so YAML does not turn them into booleans or numbers), `AWS_REGION`, log group, and key prefix defaults are added, and the migration now calls the script above. Secrets (`DATABASE_URL`, `JWT_SECRET_KEY`) are deliberately **not** in this file; you enter them in the Beanstalk console.

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    APP_ENV: "aws"
    LOG_LEVEL: "INFO"
    TRUSTED_PROXY_COUNT: "1"
    ENABLE_SANDBOX: "false"
    STATIC_DIR: "app/static"
    STORAGE_BACKEND: "s3"
    S3_KEY_PREFIX: "prod"
    AWS_REGION: "us-east-1"
    CLOUDWATCH_ENABLED: "true"
    CW_LOG_GROUP: "/api-security-monitor/app"
    CW_LOG_STREAM_PREFIX: "eb"
    CW_METRICS_NAMESPACE: "ApiSecurityMonitor"
    PORT: "5000"
  aws:elasticbeanstalk:environment:process:default:
    HealthCheckPath: /api/health
    Port: "5000"
    Protocol: HTTP

container_commands:
  01_migrate:
    command: "bash eb_migrate.sh"
    leader_only: true
```

## 8. Step 6: Replace `deploy/eb/.platform/nginx/conf.d/proxy.conf`

Replace the whole file. Beanstalk's default nginx already forwards traffic to port 5000 (your `PORT` setting) and already adds the client IP to `X-Forwarded-For`, so the custom `location` block is not needed and breaks nginx.

```nginx
# Included by Elastic Beanstalk inside the nginx 'http' block, so only http-level
# directives belong here. (The default EB nginx already proxies to the app port and
# appends the client IP to X-Forwarded-For, which TRUSTED_PROXY_COUNT=1 relies on.)
client_max_body_size 20M;
```

---

## 9. Step 7: Edit existing backend files

### 7a. `backend/app/integrations/cloudwatch.py`

**Edit 1.** Replace the entire `configure_cloudwatch_logging` function (from `def configure_cloudwatch_logging` down to just before `def emit_metric`) with:

```python
def configure_cloudwatch_logging(log_level: str = "INFO") -> None:
    """Attaches Watchtower logging handler to the operational logger if enabled.

    Credentials come from boto3's default chain (instance profile on EC2/Beanstalk,
    environment variables or ~/.aws/credentials on a laptop). Nothing is hardcoded.
    """
    if not is_cloudwatch_enabled():
        return

    try:
        import boto3
        import watchtower

        ops_logger = logging.getLogger("app.ops")
        # Avoid attaching a second CloudWatch handler if create_app() runs more than once
        if any(isinstance(h, watchtower.CloudWatchLogHandler) for h in ops_logger.handlers):
            return

        from app.core.logging_config import JsonFormatter

        log_group = os.getenv("CW_LOG_GROUP", "/api-security-monitor/app")
        stream_prefix = os.getenv("CW_LOG_STREAM_PREFIX", "local-dev")
        region = os.getenv("AWS_REGION", "us-east-1")
        hostname = socket.gethostname()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stream_name = f"{stream_prefix}-{hostname}-{today}"

        boto_client = boto3.client("logs", region_name=region)
        cw_handler = watchtower.CloudWatchLogHandler(
            log_group_name=log_group,
            log_stream_name=stream_name,
            boto3_client=boto_client,
            send_interval=10,
        )
        cw_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        # Ship the same one-line JSON the console handler prints
        cw_handler.setFormatter(JsonFormatter())

        ops_logger.addHandler(cw_handler)
    except Exception as exc:
        print(f"[WARN] Failed to configure CloudWatch logging: {exc}", file=sys.stderr)
```

**Edit 2.** Append this to the very end of the file (after `flush_metrics`):

```python
_FLUSH_THREAD: Optional[threading.Thread] = None
_FLUSH_STOP = threading.Event()


def start_metrics_flusher() -> None:
    """Starts a daemon thread that flushes buffered metrics every CW_METRICS_FLUSH_SECONDS."""
    global _FLUSH_THREAD
    if not is_cloudwatch_enabled():
        return
    if _FLUSH_THREAD is not None and _FLUSH_THREAD.is_alive():
        return

    interval = max(10, int(os.getenv("CW_METRICS_FLUSH_SECONDS", "60")))
    _FLUSH_STOP.clear()

    def _loop() -> None:
        while not _FLUSH_STOP.wait(interval):
            flush_metrics()

    _FLUSH_THREAD = threading.Thread(target=_loop, name="cw-metrics-flusher", daemon=True)
    _FLUSH_THREAD.start()


def stop_metrics_flusher() -> None:
    """Stops the flusher thread and pushes any remaining buffered metrics."""
    _FLUSH_STOP.set()
    flush_metrics()
```

Why: the handler now uses your JSON formatter, never attaches twice, and a background thread flushes the buffered metrics (nothing flushed them before). Existing functions and signatures are unchanged, so the existing tests in `tests/integrations/test_cloudwatch.py` keep working.

### 7b. `backend/app/main.py` (three small edits)

**Edit 1.** Add this import at the top of the imports block, above `from typing import Callable, Optional`:

```python
from contextlib import asynccontextmanager
```

**Edit 2.** Right after the line `from app.core.logging_config import configure_logging, get_ops_logger`, add:

```python
from app.integrations.cloudwatch import (
    configure_cloudwatch_logging,
    start_metrics_flusher,
    stop_metrics_flusher,
)
```

**Edit 3.** Inside `create_app`, replace this block:

```python
    # 1. Configure operational JSON logger
    configure_logging(cfg.log_level)
    ops_logger = get_ops_logger()
    ops_logger.info("application_startup", extra={"extra_fields": {"env": cfg.app_env}})

    # 2. Instantiate FastAPI app
    application = FastAPI(
        title="APEye - API Security Monitoring Platform",
```

with:

```python
    # 1. Configure operational JSON logger
    configure_logging(cfg.log_level)
    configure_cloudwatch_logging(cfg.log_level)  # no-op unless CLOUDWATCH_ENABLED=true
    ops_logger = get_ops_logger()
    ops_logger.info("application_startup", extra={"extra_fields": {"env": cfg.app_env}})

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        start_metrics_flusher()  # no-op unless CLOUDWATCH_ENABLED=true
        yield
        ops_logger.info("application_shutdown")
        stop_metrics_flusher()

    # 2. Instantiate FastAPI app
    application = FastAPI(
        lifespan=lifespan,
        title="APEye - API Security Monitoring Platform",
```

Leave the rest of the `FastAPI(...)` call and the rest of the file as it is.

### 7c. `backend/app/services/ingestion_service.py`

**Edit 1.** Below `from app.core.logging_config import get_ops_logger`, add:

```python
from app.integrations.cloudwatch import emit_metric
```

**Edit 2.** In the first `except` block, find this comment line and put the new line directly above it:

```python
            emit_metric("RequestLogWriteFailures")
            # Failure in log writing terminates ingestion without running detection
```

**Edit 3.** In the detection `except` block, directly after the closing `)` of the `ops_logger.error("detection_engine_failure", ...)` call (before `finally:`), add:

```python
            emit_metric("DetectionErrors")
```

(Indentation: 12 spaces, same level as `ops_logger.error(`.)

### 7d. `backend/app/services/alert_service.py`

**Edit 1.** Below `from app.core.logging_config import get_ops_logger`, add:

```python
from app.integrations.cloudwatch import emit_metric
```

**Edit 2.** Find:

```python
                outcomes.append(
                    AlertOutcome(action="auto_closed_and_created", alert_id=new_alert.id)
                )
```

and add one line right after it (16 spaces of indentation):

```python
                emit_metric("AlertsCreated")
```

**Edit 3.** Find:

```python
                outcomes.append(AlertOutcome(action="created", alert_id=new_alert.id))
```

and add the same line right after it (16 spaces):

```python
                emit_metric("AlertsCreated")
```

### 7e. `backend/app/services/report_service.py`

**Edit 1.** Above `from app.integrations.storage import generate_report_object_key, get_storage`, add:

```python
from app.integrations.cloudwatch import emit_metric
```

**Edit 2.** Replace:

```python
    info = storage.upload_bytes(
        key=object_key,
        data=payload,
        content_type=content_type,
        metadata=metadata,
    )
```

with:

```python
    try:
        info = storage.upload_bytes(
            key=object_key,
            data=payload,
            content_type=content_type,
            metadata=metadata,
        )
    except Exception:
        emit_metric("ReportUploadsFailed")
        raise
```

### 7f. `backend/.env.example`

Replace these three lines:

```text
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

with:

```text
AWS_REGION=us-east-1
# Do NOT set AWS keys on EC2/Elastic Beanstalk in Learner Lab: the attached instance profile
# supplies temporary credentials automatically (boto3 default credential chain).
# Only for testing S3/CloudWatch from your own laptop, paste the Learner Lab 'AWS Details' values:
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_SESSION_TOKEN=
```

---

## 10. Step 8: Add a test for the new flusher

New file `backend/tests/integrations/test_cloudwatch_flusher.py`:

```python
"""Tests for the periodic CloudWatch metrics flusher (added for AWS deployment)."""

from moto import mock_aws

from app.integrations import cloudwatch
from app.integrations.cloudwatch import start_metrics_flusher, stop_metrics_flusher


def test_flusher_is_noop_when_cloudwatch_disabled(monkeypatch):
    monkeypatch.setenv("CLOUDWATCH_ENABLED", "false")
    start_metrics_flusher()
    assert cloudwatch._FLUSH_THREAD is None or not cloudwatch._FLUSH_THREAD.is_alive()
    stop_metrics_flusher()


@mock_aws
def test_flusher_starts_and_stops_when_enabled(monkeypatch):
    monkeypatch.setenv("CLOUDWATCH_ENABLED", "true")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    start_metrics_flusher()
    assert cloudwatch._FLUSH_THREAD is not None and cloudwatch._FLUSH_THREAD.is_alive()
    cloudwatch.emit_metric("AlertsCreated")
    stop_metrics_flusher()
    cloudwatch._FLUSH_THREAD.join(timeout=5)
    assert not cloudwatch._FLUSH_THREAD.is_alive()
```

## 11. Step 9: Add `scripts/aws_smoke_test.py` (new file)

Standard-library-only post-deployment check. With `--traffic` it sends controlled bursts that should produce all four alert types, so use it only against your own deployment.

```python
#!/usr/bin/env python3
"""Post-deployment smoke test for APEye (standard library only).

Usage:
  python scripts/aws_smoke_test.py --base-url http://YOUR-ENV.elasticbeanstalk.com --username admin
  python scripts/aws_smoke_test.py --base-url http://... --username admin --traffic

--traffic sends controlled bursts that should trigger all four alert types. Only run it
against YOUR OWN deployment. The password is read from APEYE_SMOKE_PASSWORD or prompted.
"""

import argparse
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

RESULTS = []


def call(base, method, path, token=None, body=None, raw_url=None, timeout=30):
    url = raw_url or base.rstrip("/") + path
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read()
    except Exception as exc:  # network problem
        return 0, {}, str(exc).encode()


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def jbody(raw):
    try:
        return json.loads(raw)
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--username", default="admin")
    ap.add_argument("--traffic", action="store_true", help="generate suspicious test traffic")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    password = os.getenv("APEYE_SMOKE_PASSWORD") or getpass.getpass(f"Password for {args.username}: ")

    st, _, raw = call(base, "GET", "/api/health")
    check("health ok and database ok", st == 200 and jbody(raw).get("database") == "ok", f"(HTTP {st})")

    st, _, raw = call(base, "GET", "/")
    check("React index served at /", st == 200 and b'id="root"' in raw, f"(HTTP {st})")
    st, _, raw = call(base, "GET", "/alerts")
    check("deep link /alerts served", st == 200 and b'id="root"' in raw, f"(HTTP {st})")

    st, _, raw = call(base, "GET", "/api/dashboard/summary")
    check("protected endpoint rejects anonymous (401)", st == 401, f"(HTTP {st})")

    st, _, raw = call(base, "POST", "/api/auth/login", body={"username": args.username, "password": password})
    token = jbody(raw).get("access_token")
    check("login returns token", st == 200 and bool(token), f"(HTTP {st})")
    if not token:
        print("Cannot continue without a token."); sys.exit(1)

    st, _, raw = call(base, "GET", "/api/auth/me", token)
    check("/api/auth/me", st == 200 and jbody(raw).get("role") == "ADMIN", f"(HTTP {st})")
    st, _, raw = call(base, "GET", "/api/dashboard/summary", token)
    check("dashboard summary", st == 200, f"(HTTP {st})")

    if args.traffic:
        print("--- sending controlled test traffic to your own deployment ---")
        for i in range(12):  # brute force: more than 10 failed logins
            call(base, "POST", "/api/auth/login", body={"username": "nobody", "password": f"wrong-{i}"})
        for i in range(25):  # reconnaissance: many distinct 404 paths
            call(base, "GET", f"/api/probe/path-{i}")
        for p in ("/api/admin", "/api/.env", "/api/config", "/api/backup"):
            call(base, "GET", p)
        for _ in range(20):  # repeated unauthorized: more than 15 x 401
            call(base, "GET", "/api/dashboard/summary")
        for _ in range(110):  # request rate: more than 100 in 60 s
            call(base, "GET", "/api/auth/me")
        time.sleep(3)
        st, _, raw = call(base, "GET", "/api/alerts?page_size=100", token)
        cats = sorted({a.get("category") for a in jbody(raw).get("items", [])})
        want = {"BRUTE_FORCE", "EXCESSIVE_REQUESTS", "RECONNAISSANCE", "UNAUTHORIZED_ACCESS"}
        check("all four alert categories present", want.issubset(set(cats)), f"(found {cats})")

    st, _, raw = call(base, "GET", "/api/logs?page_size=5", token)
    check("logs endpoint returns rows", st == 200 and jbody(raw).get("total_items", 0) > 0, f"(HTTP {st})")

    st, hdr, raw = call(base, "GET", "/api/exports/logs.csv", token)
    check("logs CSV export", st == 200 and "csv" in str(hdr.get("Content-Type", "")), f"(HTTP {st})")

    now = datetime.now(timezone.utc)
    body = {
        "report_type": "SUMMARY",
        "from": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    st, _, raw = call(base, "POST", "/api/reports/archive", token, body)
    arch = jbody(raw)
    check("archive report", st == 201 and "id" in arch, f"(HTTP {st}, backend={arch.get('storage_backend')})")
    if st == 201:
        st, _, raw = call(base, "GET", f"/api/reports/{arch['id']}/download", token)
        url = jbody(raw).get("url", "")
        check("download link issued", st == 200 and bool(url), f"(HTTP {st})")
        if arch.get("storage_backend") == "s3" and url.startswith("http"):
            st, _, _ = call(base, "GET", None, raw_url=url)
            check("presigned URL downloads the object", st == 200, f"(HTTP {st})")
            st, _, _ = call(base, "GET", None, raw_url=url.split("?")[0])
            check("bare S3 object URL is denied (private bucket)", st in (403, 404), f"(HTTP {st})")

    print(f"\n{sum(RESULTS)}/{len(RESULTS)} checks passed")
    print("Manual checks: CloudWatch log group shows alert_created events; metrics namespace "
          "ApiSecurityMonitor appears; RDS is not reachable from your laptop.")
    sys.exit(0 if all(RESULTS) else 1)


if __name__ == "__main__":
    main()
```

---

## 12. Step 10: Verify locally before you touch AWS

Run these from the repo root. Everything must still behave exactly as before.

```bash
# 1. Backend lint and tests (local PostgreSQL must be running, as before)
cd backend
ruff check .
pytest -q
cd ..

# 2. Frontend checks (unchanged code, but confirm the build is still healthy)
cd frontend
npm ci
npm run lint
npm run test
cd ..

# 3. Build the release zips
python scripts/build_release.py
```

Expected result of step 3: the last lines say `OK: apeye-eb.zip layout verified` and list both zips in `dist/`.

Quick look inside the Beanstalk zip (the first entries must be `Procfile`, `requirements.txt`, `app/`, and `.ebextensions/`, with **no** `backend/` folder):

```bash
python -c "import zipfile; z=zipfile.ZipFile('dist/apeye-eb.zip'); print(sorted({n.split('/')[0] for n in z.namelist()}))"
```

Optional but recommended: start the app locally once with the new code to confirm nothing broke:

```bash
cd backend
uvicorn app.main:app --port 8000
# then open http://localhost:8000/api/health
```

If any test fails after these edits, the most likely cause is an indentation slip in Step 7c or 7d; compare your file to the snippets above.

## 13. Step 11: Commit

```bash
git add -A
git status          # confirm: no .env, no dist/, no backend/app/static files
git commit -m "chore(deploy): Learner Lab deployment changes (cross-platform build, EB fixes, CloudWatch wiring)"
```

`dist/` and `backend/app/static/*` are already git-ignored by your `.gitignore`.

---

## 14. Things I deliberately did not change (and why)

- **No AWS keys anywhere in code.** On Beanstalk and EC2, credentials come from the instance profile you select in the console.
- **Frontend code.** It already uses relative `/api` and is served by FastAPI from the same origin.
- **`deploy/ec2/setup.sh`.** It works as written if you follow the guide's Ubuntu steps (the guide adds one nginx fix after running it).
- **Database migrations and models.** Untouched.
- **`seed_demo_data.py`.** It stays in the repo but is not packaged for AWS (see P8). If you want demo data in the cloud later, set `ADMIN_PASSWORD` first and change the `analyst` password immediately from the Users page.

## 15. Known local-only quirks I noticed (optional to fix)

These do not affect AWS but may confuse teammates:

- The code reads environment variables with `os.getenv` and does **not** load `backend/.env` automatically, so locally you must export the values (or start with `uvicorn --env-file .env`). On AWS the platform supplies them.
- `docker-compose.yml` maps PostgreSQL to host port **5433**, while the default `DATABASE_URL` and the README use **5432**. Set `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/apimonitor` locally, or change the compose port mapping to `5432:5432`.
- The Learner Lab session limit, stopped instances after a session ends, and HTTP-only access (no HTTPS without a load balancer and certificate) are covered in the deployment guide.

## 16. Optional hardening (recommended before a public demo)

Refuse to start on AWS with the default JWT secret. In `backend/app/main.py`, at the top of `create_app`, after `cfg = settings or get_settings()`, add:

```python
    if cfg.app_env == "aws":
        from app.auth.config import get_auth_settings

        if get_auth_settings().jwt_secret_key.startswith("replace-with-a-random"):
            raise RuntimeError("JWT_SECRET_KEY must be set to a random value on AWS")
```

If you add it, make sure `JWT_SECRET_KEY` is set in Beanstalk (the deployment guide does this) or the environment will fail health checks on purpose.
