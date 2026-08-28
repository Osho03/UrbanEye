#!/usr/bin/env bash
# UrbanEye Backend - Oracle Cloud Always Free deployment setup
# Run once on a fresh Ubuntu 24.04 (ARM) Oracle Cloud instance.
set -euo pipefail

echo "============================================"
echo " UrbanEye Backend - Oracle Cloud Setup"
echo "============================================"

# --- 1. System packages ---
echo "[1/6] Installing system packages..."
sudo apt-get update -y
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev gcc g++ make \
    libgl1 libglib2.0-0 git curl
# opencv-python-headless needs libglib + libgl on some systems (ARM handled above)

# --- 2. Clone the repo (or copy it up) ---
# NOTE: If you already copied the "backend" folder, skip cloning and cd instead.
if [ ! -d "UrbanEye" ]; then
  echo "[2/6] Cloning repository..."
  git clone https://github.com/Osho03/UrbanEye.git
  cd UrbanEye/backend
else
  cd UrbanEye/backend
fi

# --- 3. Python virtualenv + deps ---
echo "[3/6] Creating virtualenv and installing Python dependencies..."
python3.11 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
# Oracle Always Free is ARM (aarch64) - PyPI ships CPU wheels for it already.
# On x86_64 we use the official CPU-only index to keep the install light.
if uname -m | grep -q aarch64; then
  pip install torch torchvision
else
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
fi
pip install -r requirements.txt

# --- 4. Environment variables ---
echo "[4/6] Writing .env (edit this file with your real keys)..."
if [ ! -f .env ]; then
  cat > .env <<'EOF'
# UrbanEye - Oracle Cloud
# >>> EDIT THESE with your real values <<<
MONGO_URI=mongodb+srv://oshomani2006_db_user:YOUR_MONGO_PASSWORD@cluster0.o4vinqh.mongodb.net/?retryWrites=true&writes=true&appName=cluster0
GEMINI_API_KEY=AIzaSyA5Cei2ld_I2BQU8qvVdJ-SnOJL-SJfL6s
PORT=5000
EOF
  echo "  -> Created .env - open it and set MONGO_URI password + GEMINI key"
else
  echo "  -> .env already exists, leaving it"
fi

# --- 5. systemd service (auto-start, always-on, auto-restart) ---
echo "[5/6] Installing systemd service..."
sudo tee /etc/systemd/system/urbaneye.service > /dev/null <<'SVC'
[Unit]
Description=UrbanEye Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/UrbanEye/backend
ExecStart=/home/ubuntu/UrbanEye/backend/.venv/bin/gunicorn -b 0.0.0.0:5000 -c gunicorn_config.py app:app
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/UrbanEye/backend/.env
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVC

sudo systemctl daemon-reload
sudo systemctl enable urbaneye
sudo systemctl start urbaneye

# --- 6. Firewall (open port 5000) ---
echo "[6/6] Opening firewall port 5000..."
# Oracle Cloud uses iptables via Security Lists; on top we open the OS firewall.
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow 5000/tcp || true
fi

echo ""
echo "============================================"
echo " DONE. Checking service status..."
echo "============================================"
sleep 4
sudo systemctl status urbaneye --no-pager || true
echo ""
echo "--------------------------------------------"
echo " Your backend is now running."
echo " Public URL: http://<YOUR_INSTANCE_PUBLIC_IP>:5000"
echo ""
echo " Then UPDATE the app:"
echo "   mobile/lib/services/api_service.dart"
echo "   baseUrl = 'http://<YOUR_INSTANCE_PUBLIC_IP>:5000'"
echo "--------------------------------------------"
