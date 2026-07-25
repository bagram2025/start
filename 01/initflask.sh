#!/bin/bash
# --------------------------------------------------------------
# Установка окружения для Flask-приложений (web_admin.py и др.)
# --------------------------------------------------------------
set -euo pipefail

APP_DIR="/home/buser/web_admin"

echo "=== [1/3] Установка системных пакетов ==="
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

echo "=== [2/3] Создание виртуального окружения ==="
mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Виртуальное окружение создано."
else
    echo "Виртуальное окружение уже существует."
fi

source venv/bin/activate

echo "=== [3/3] Установка Flask и g4f ==="
pip install --upgrade pip
pip install flask g4f

echo ""
echo "=============================================="
echo "  ГОТОВО!"
echo "  Flask и g4f установлены в $APP_DIR/venv"
echo ""
echo "  Для ручного запуска:"
echo "  cd $APP_DIR"
echo "  source venv/bin/activate"
echo "  python3 webadmin.py"
echo "=============================================="
