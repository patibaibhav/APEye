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
