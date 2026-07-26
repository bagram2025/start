#!/bin/bash
# --------------------------------------------------------------
# Настройка Nginx и портала для сервера Бусера
# Запускать из папки с portal.py и web_admin.py
# --------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORTAL_FILE="$SCRIPT_DIR/portal.py"
ADMIN_FILE="$SCRIPT_DIR/web_admin.py"
NGINX_CONF="/etc/nginx/sites-available/buser"
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "=== [1/6] Проверка файлов ==="
if [ ! -f "$PORTAL_FILE" ]; then
    echo "❌ portal.py не найден в $SCRIPT_DIR"
    exit 1
fi
if [ ! -f "$ADMIN_FILE" ]; then
    echo "⚠️ web_admin.py не найден. AI-админ не будет работать по /admin"
fi

echo "=== [2/6] Установка Nginx ==="
sudo apt-get update
sudo apt-get install -y nginx

echo "=== [3/6] Виртуальное окружение для портала ==="
if [ ! -d "$SCRIPT_DIR/venv_portal" ]; then
    python3 -m venv "$SCRIPT_DIR/venv_portal"
fi
source "$SCRIPT_DIR/venv_portal/bin/activate"
pip install --upgrade pip
pip install flask

echo "=== [4/6] Конфигурация Nginx ==="
sudo tee "$NGINX_CONF" <<EOF
# Главная страница-портал
server {
    listen 80;
    server_name _;

    # Портал
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # AI-Администратор
    location /admin {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Активируем сайт
sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "=== [5/6] Systemd-сервисы ==="

# Портал
sudo tee /etc/systemd/system/portal.service <<EOF
[Unit]
Description=Portal Page
After=network.target

[Service]
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv_portal/bin/python3 $PORTAL_FILE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# AI-админ (если есть)
if [ -f "$ADMIN_FILE" ]; then
    sudo tee /etc/systemd/system/web_admin.service <<EOF
[Unit]
Description=Web Admin AI (Buser)
After=network.target

[Service]
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python3 $ADMIN_FILE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi

echo "=== [6/6] Запуск ==="
sudo systemctl daemon-reload
sudo systemctl enable --now portal
if [ -f "$ADMIN_FILE" ]; then
    sudo systemctl enable --now web_admin
fi
sudo nginx -t
sudo systemctl restart nginx

# Фаервол
sudo ufw allow 80/tcp

echo ""
echo "=============================================="
echo "  ГОТОВО!"
echo "  Портал:     http://$SERVER_IP"
echo "  AI-Админ:   http://$SERVER_IP/admin"
echo ""
echo "  Проверка:"
echo "  curl http://localhost:5001  # портал"
echo "  curl http://localhost:5000  # админ"
echo "=============================================="
