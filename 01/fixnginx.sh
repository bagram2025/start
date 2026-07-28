#!/bin/bash
# --------------------------------------------------------------
# Полный фикс: Nginx + портал + админ-панель + AI-админ
# Запускать из папки start/01
# --------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== [1/4] Окружения ==="

# Портал
if [ ! -d "venv_portal" ]; then
    python3 -m venv venv_portal
fi
source venv_portal/bin/activate
pip install flask --quiet
deactivate

# Админ-панель
if [ ! -d "venv_panel" ]; then
    python3 -m venv venv_panel
fi
source venv_panel/bin/activate
pip install flask --quiet
deactivate

# AI-админ
if [ -f "web_admin.py" ] && [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install flask requests g4f --quiet
    deactivate
fi

echo "=== [2/4] Остановка старых процессов ==="
pkill -f "python3 portal.py" 2>/dev/null || true
pkill -f "python3 panel.py" 2>/dev/null || true
pkill -f "python3 web_admin.py" 2>/dev/null || true
sleep 1

echo "=== [3/4] Запуск ==="

# Портал (5001)
if [ -f "portal.py" ]; then
    source venv_portal/bin/activate
    nohup python3 portal.py > /tmp/portal.log 2>&1 &
    echo "✅ Портал запущен (PID $!)"
    deactivate
fi

# Админ-панель (5002)
if [ -f "panel.py" ]; then
    source venv_panel/bin/activate
    nohup python3 panel.py > /tmp/panel.log 2>&1 &
    echo "✅ Панель запущена (PID $!)"
    deactivate
fi

# AI-админ (5000)
if [ -f "web_admin.py" ]; then
    source venv/bin/activate
    nohup python3 web_admin.py > /tmp/web_admin.log 2>&1 &
    echo "✅ AI-админ запущен (PID $!)"
    deactivate
fi

sleep 2

echo "=== [4/4] Nginx ==="

sudo tee /etc/nginx/sites-available/buser <<'NGINX'
server {
    listen 80;
    server_name _;

    # Портал
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # AI-Админ
    location /admin {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Админ-панель
    location /panel {
        proxy_pass http://127.0.0.1:5002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/buser /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
sudo ufw allow 80/tcp 2>/dev/null || true

echo ""
echo "=============================================="
echo "  ГОТОВО!"
echo "  Главная:    http://$(hostname -I | awk '{print $1}')"
echo "  Админ:      http://$(hostname -I | awk '{print $1}')/admin"
echo "  Панель:     http://$(hostname -I | awk '{print $1}')/panel"
echo ""
echo "  Проверка:"
echo "  curl http://127.0.0.1:5001  # портал"
echo "  curl http://127.0.0.1:5000  # админ"
echo "  curl http://127.0.0.1:5002  # панель"
echo "=============================================="
