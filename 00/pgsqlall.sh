#!/bin/bash
# --------------------------------------------------------------
# Открытие PostgreSQL для внешних подключений
# --------------------------------------------------------------
set -euo pipefail

# Настройки (поменяйте при необходимости)
ALLOWED_IP="0.0.0.0/0"        # С каких IP разрешены подключения.
                               # 0.0.0.0/0 — со всего мира (опасно!)
                               # Лучше указать свой IP: 123.123.123.123/32
PG_USER="test"                 # Какому пользователю разрешён внешний доступ
PG_PORT=5432

echo "=== [1/4] Настройка postgresql.conf ==="
PG_CONF=$(sudo -u postgres psql -tAc "SHOW config_file;")
echo "Файл конфигурации: $PG_CONF"

# Раскомментируем и меняем listen_addresses
sudo sed -i "s/^#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"
# На случай если уже было изменено
sudo sed -i "s/^listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"

echo "listen_addresses установлен в '*'"

echo "=== [2/4] Настройка pg_hba.conf ==="
HBA_CONF=$(sudo -u postgres psql -tAc "SHOW hba_file;")
echo "Файл аутентификации: $HBA_CONF"

# Добавляем правило для внешних подключений, если его ещё нет
if ! grep -q "host.*all.*$PG_USER.*$ALLOWED_IP.*md5" "$HBA_CONF"; then
    echo "host    all             $PG_USER        $ALLOWED_IP        md5" | sudo tee -a "$HBA_CONF"
    echo "Правило для внешнего доступа добавлено."
else
    echo "Правило уже существует."
fi

echo "=== [3/4] Открытие порта в фаерволе ==="
sudo ufw allow $PG_PORT/tcp
echo "Порт $PG_PORT открыт."

echo "=== [4/4] Перезапуск PostgreSQL ==="
sudo systemctl restart postgresql

echo "----------------------------------------"
echo "ГОТОВО! Внешний доступ к PostgreSQL открыт."
echo ""
echo "Данные для подключения:"
echo "  Хост:     $(hostname -I | awk '{print $1}')"
echo "  Порт:     $PG_PORT"
echo "  База:     test"
echo "  Польз-ль: $PG_USER"
echo "  Пароль:   test"
echo ""
echo "Строка подключения:"
echo "  psql -h $(hostname -I | awk '{print $1}') -p $PG_PORT -U $PG_USER -d test"
echo "----------------------------------------"
