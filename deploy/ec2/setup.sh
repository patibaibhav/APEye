#!/usr/bin/env bash
# ==============================================================================
# setup.sh - EC2 rehearsal host setup script (Owner: Baibhav)
# Target OS: Amazon Linux 2023 / Ubuntu 22.04+
# Sets up Python runtime, systemd service, nginx proxy, and runs migrations.
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/apeye"
APP_USER="apeye"
VENV_DIR="${APP_DIR}/backend/.venv"

echo "=== [1/6] Installing system packages ==="
if command -v dnf &>/dev/null; then
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip python3-devel nginx git libpq-devel
elif command -v apt-get &>/dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv nginx git libpq-dev
fi

echo "=== [2/6] Creating application user and directories ==="
if ! id "${APP_USER}" &>/dev/null; then
    sudo useradd -r -s /bin/false -d "${APP_DIR}" "${APP_USER}"
fi

sudo mkdir -p "${APP_DIR}"
sudo chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "=== [3/6] Setting up Python virtual environment ==="
sudo -u "${APP_USER}" python3 -m venv "${VENV_DIR}"
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip
sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"

echo "=== [4/6] Creating systemd service ==="
sudo tee /etc/systemd/system/apeye.service > /dev/null <<EOF
[Unit]
Description=APEye API Security Monitoring Service
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}/backend
EnvironmentFile=${APP_DIR}/backend/.env
ExecStart=${VENV_DIR}/bin/uvicorn app.main:app --host 127.0.0.1 --port 5000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo "=== [5/6] Configuring Nginx reverse proxy ==="
sudo tee /etc/nginx/conf.d/apeye.conf > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
EOF

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "=== [6/6] Database migrations and service launch ==="
if [ -f "${APP_DIR}/backend/.env" ]; then
    echo "Running Alembic migrations..."
    sudo -u "${APP_USER}" bash -c "cd ${APP_DIR}/backend && set -a && source .env && set +a && ${VENV_DIR}/bin/alembic upgrade head"
    echo "Starting apeye service..."
    sudo systemctl enable apeye
    sudo systemctl restart apeye
    echo "APEye service successfully deployed and running on port 80."
else
    echo "WARNING: ${APP_DIR}/backend/.env not found. Please populate environment variables and run migrations."
fi
