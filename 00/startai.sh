#!/bin/bash
# --------------------------------------------------------------
# Установка окружения и запуск AI-помощника (ai_admin.py)
# --------------------------------------------------------------
set -euo pipefail

echo "=== [1/4] Обновление пакетов ==="
sudo apt-get update

echo "=== [2/4] Установка Python и pip ==="
sudo apt-get install -y python3 python3-pip python3-venv

echo "=== [3/4] Создание виртуального окружения ==="
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Виртуальное окружение создано."
else
    echo "Виртуальное окружение уже существует."
fi

source venv/bin/activate

echo "=== [4/4] Установка g4f и запуск AI-помощника ==="
pip install --upgrade pip
pip install g4f

echo ""
echo "=============================================="
echo "  Запуск AI-помощника Бусер..."
echo "=============================================="
echo ""

python3 aiadmin.py
