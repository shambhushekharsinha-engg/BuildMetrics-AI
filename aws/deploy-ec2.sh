#!/usr/bin/env bash
# ==============================================================================
# BuildMetrics AI v2.0.0 — EC2 Deployment Script
# Targets: Ubuntu 22.04 LTS / Debian 12 / Amazon Linux 2023
# ==============================================================================

set -euo pipefail

echo "=================================================================="
echo "🏗️  BuildMetrics AI v2.0.0 — Automated AWS EC2 Deployment Setup"
echo "=================================================================="

# Check root or sudo
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root or with sudo: sudo ./deploy-ec2.sh"
  exit 1
fi

# 1. Update OS Packages
echo "[1/6] Updating system packages..."
apt-get update -y && apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg lsb-release git ufw

# 2. Install Docker & Docker Compose
echo "[2/6] Installing Docker Engine & Compose plugin..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

# Add non-root user (ubuntu or ec2-user) to docker group
TARGET_USER="ubuntu"
if ! id "$TARGET_USER" &>/dev/null; then
    TARGET_USER="${SUDO_USER:-$USER}"
fi
usermod -aG docker "$TARGET_USER" || true

# 3. Setup Project Directory
echo "[3/6] Setting up project repository..."
APP_DIR="/opt/buildmetrics-ai"
if [ -d "$APP_DIR" ]; then
    echo "Directory exists, pulling latest changes..."
    cd "$APP_DIR"
    git fetch origin main
    git reset --hard origin/main
else
    echo "Cloning repository..."
    git clone https://github.com/shambhushekharsinha-engg/BuildMetrics-AI.git "$APP_DIR"
    cd "$APP_DIR"
fi

chown -R "$TARGET_USER":"$TARGET_USER" "$APP_DIR"

# 4. Configure Production Environment (.env)
echo "[4/6] Configuring production environment..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat << 'EOF' > "$APP_DIR/.env"
ENVIRONMENT=production
DATABASE_URL=sqlite:///buildmetrics.db
REDIS_URL=redis://redis:6379
SHARED_EXPORT_DIR=/app/exports
ALLOWED_ORIGINS=*
API_BASE_URL=http://localhost:8000
GEMINI_API_KEY=
EOF
    echo "[+] Default .env created. Remember to add your GEMINI_API_KEY if needed."
fi

# 5. Build and Launch Containers
echo "[5/6] Building images and launching containers..."
cd "$APP_DIR"
docker compose down --remove-orphans || true
docker compose up -d --build

# 6. Configure Systemd Service
echo "[6/6] Configuring systemd persistence service..."
cat << EOF > /etc/systemd/system/buildmetrics.service
[Unit]
Description=BuildMetrics AI Docker Compose Stack
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable buildmetrics.service

# Get Public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || curl -s ifconfig.me || echo "your-server-ip")

echo "=================================================================="
echo "🎉 BuildMetrics AI v2.0.0 is live and running!"
echo "   Streamlit Studio:  http://$PUBLIC_IP:8501"
echo "   FastAPI Swagger:   http://$PUBLIC_IP:8000/docs"
echo "   Health Probe:      http://$PUBLIC_IP:8000/healthz"
echo "=================================================================="
