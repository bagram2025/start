#!/bin/bash
# --------------------------------------------------------------
# Запуск портала и AI-админа вручную (без systemd)
# Запускать из папки start/01
# --------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Рабочая папка: $SCRIPT_DIR"

# Проверка файлов
if [ ! -f "$SCRIPT_DIR/portal.py" ]; then
    echo "❌ portal.py не найден. Положите его в $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/web_admin.py" ]; then
    echo "⚠️ web_admin.py не найден — AI-админ не запустится."
fi

echo "=== [1/2] Настройка окружения ==="

# Окружение для портала
if [ ! -d "$SCRIPT_DIR/venv_portal" ]; then
    python3 -m venv "$SCRIPT_DIR/venv_portal"
fi
source "$SCRIPT_DIR/venv_portal/bin/activate"
pip install --upgrade pip --quiet
pip install flask --quiet
echo "✓ Окружение портала готово"
deactivate

# Окружение для админа
if [ -f "$SCRIPT_DIR/web_admin.py" ]; then
    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        python3 -m venv "$SCRIPT_DIR/venv"
    fi
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install --upgrade pip --quiet
    pip install flask requests --quiet
    echo "✓ Окружение админа готово"
    deactivate
fi

echo "=== [2/2] Запуск ==="

# Запуск портала в фоне
echo "Запуск портала на порту 5001..."
source "$SCRIPT_DIR/venv_portal/bin/activate"
nohup python3 "$SCRIPT_DIR/portal.py" > /tmp/portal.log 2>&1 &
PORTAL_PID=$!
echo "  PID портала: $PORTAL_PID"
deactivate

# Запуск админа в фоне
if [ -f "$SCRIPT_DIR/web_admin.py" ]; then
    echo "Запуск AI-админа на порту 5000..."
    source "$SCRIPT_DIR/venv/bin/activate"
    nohup python3 "$SCRIPT_DIR/web_admin.py" > /tmp/web_admin.log 2>&1 &
    ADMIN_PID=$!
    echo "  PID админа: $ADMIN_PID"
    deactivate
fi

sleep 2

# Проверка
echo ""
echo "=== Проверка ==="
if curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5001 | grep -q 200; then
    echo "✅ Портал:    http://$(hostname -I | awk '{print $1}')"
else
    echo "❌ Портал не отвечает. Лог: /tmp/portal.log"
fi

if [ -f "$SCRIPT_DIR/web_admin.py" ]; then
    if curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000 | grep -q 200; then
        echo "✅ AI-Админ:  http://$(hostname -I | awk '{print $1}')/admin"
    else
        echo "❌ Админ не отвечает. Лог: /tmp/web_admin.log"
    fi
fi

echo ""
echo "Остановить: kill $PORTAL_PID ${ADMIN_PID:-}"
echo "Логи:      tail -f /tmp/portal.log /tmp/web_admin.log"
