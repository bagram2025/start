#!/bin/bash
# --------------------------------------------------------------
# Деплой веб-версии Бусера без домена (по IP, только HTTP)
# --------------------------------------------------------------
set -euo pipefail

APP_DIR="/home/buser/web_admin"
SERVICE_NAME="web_admin"
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "=== [1/5] Установка пакетов ==="
sudo apt-get update
sudo apt-get install -y nginx python3-pip python3-venv

echo "=== [2/5] Настройка приложения ==="
mkdir -p "$APP_DIR"
cp web_admin.py "$APP_DIR/"
cd "$APP_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install flask g4f

echo "=== [3/5] Systemd-сервис ==="
sudo tee /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Web Admin AI (Бусер)
After=network.target

[Service]
User=buser
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python3 $APP_DIR/web_admin.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

echo "=== [4/5] Nginx ==="
sudo tee /etc/nginx/sites-available/buser <<EOF
server {
    listen 80;
    server_name $SERVER_IP;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/buser /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=== [5/5] Фаервол ==="
sudo ufw allow 80/tcp

echo ""
echo "=============================================="
echo "  ГОТОВО!"
echo "  Бусер доступен по адресу:"
echo "  http://$SERVER_IP"
echo "=============================================="
