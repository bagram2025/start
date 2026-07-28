#!/bin/bash
# --------------------------------------------------------------
# Исправление конфига Nginx для портала и AI-админа
# --------------------------------------------------------------
set -euo pipefail

echo "=== [1/3] Проверка запущенных сервисов ==="

# Проверяем портал
if curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5001 | grep -q 200; then
    echo "✅ Портал (5001) отвечает"
else
    echo "❌ Портал не отвечает на 5001. Запустите его:"
    echo "   cd /home/buser/projects/start/01"
    echo "   source venv_portal/bin/activate"
    echo "   nohup python3 portal.py > /tmp/portal.log 2>&1 &"
fi

# Проверяем админа
if curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000 | grep -q 200; then
    echo "✅ Админ (5000) отвечает"
else
    echo "❌ Админ не отвечает на 5000. Запустите его:"
    echo "   cd /home/buser/projects/start/01"
    echo "   source venv/bin/activate"
    echo "   nohup python3 web_admin.py > /tmp/web_admin.log 2>&1 &"
fi

echo "=== [2/3] Настройка Nginx ==="

sudo tee /etc/nginx/sites-available/buser <<'EOF'
server {
    listen 80;
    server_name _;

    # Портал (главная)
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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Активируем
sudo ln -sf /etc/nginx/sites-available/buser /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "=== [3/3] Проверка и перезапуск ==="

# Проверка конфига
if sudo nginx -t; then
    sudo systemctl restart nginx
    echo "✅ Nginx перезапущен"
else
    echo "❌ Ошибка в конфиге Nginx"
    exit 1
fi

# Фаервол
sudo ufw allow 80/tcp 2>/dev/null || true

echo ""
echo "=============================================="
echo "  ГОТОВО!"
echo "  Портал:    http://$(hostname -I | awk '{print $1}')"
echo "  Админ:     http://$(hostname -I | awk '{print $1}')/admin"
echo "=============================================="
