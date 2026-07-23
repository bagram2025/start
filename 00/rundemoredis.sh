#!/bin/bash
# --------------------------------------------------------------
# Установка окружения и запуск redisdemo.py
# --------------------------------------------------------------
set -euo pipefail

echo "=== [1/3] Установка pip и виртуального окружения ==="
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

echo "=== [2/3] Создание виртуального окружения ==="
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Виртуальное окружение создано."
else
    echo "Виртуальное окружение уже существует."
fi

# Активируем окружение
source venv/bin/activate

echo "=== [3/3] Установка redis-py и запуск демо ==="
pip install redis

echo ""
echo "Запуск redisdemo.py..."
echo "=========================="
python3 redisdemo.py
