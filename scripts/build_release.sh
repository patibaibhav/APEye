#!/usr/bin/env bash
# ==============================================================================
# build_release.sh - Packages APEye prototype for deployment (Owner: Baibhav)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
STATIC_TARGET="${ROOT_DIR}/backend/app/static"

echo "=== [1/4] Building Frontend ==="
cd "${ROOT_DIR}/frontend"
npm ci
npm run build

echo "=== [2/4] Syncing Frontend to Backend Static Directory ==="
mkdir -p "${STATIC_TARGET}"
rm -rf "${STATIC_TARGET:?}"/*
cp -r "${ROOT_DIR}/frontend/dist/"* "${STATIC_TARGET}/"

if [ ! -f "${STATIC_TARGET}/index.html" ]; then
    echo "ERROR: index.html not found in ${STATIC_TARGET}" >&2
    exit 1
fi
echo "Static assets synced successfully."

echo "=== [3/4] Preparing Deployment Artifact ==="
mkdir -p "${DIST_DIR}"
RELEASE_ZIP="${DIST_DIR}/apeye-release.zip"
rm -f "${RELEASE_ZIP}"

cd "${ROOT_DIR}"
# Archive backend app, migrations, Procfile, requirements, and deployment configs
zip -q -r "${RELEASE_ZIP}" backend/ deploy/ \
    -x "backend/.venv/*" \
    -x "backend/.pytest_cache/*" \
    -x "backend/**/__pycache__/*" \
    -x "backend/tests/*" \
    -x "backend/.env" \
    -x "backend/.local_storage/*"

echo "=== [4/4] Release Package Created ==="
echo "Artifact: ${RELEASE_ZIP}"
echo "Size: $(du -h "${RELEASE_ZIP}" | cut -f1)"
echo "Build complete."
