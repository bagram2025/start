#!/bin/bash
# --------------------------------------------------------------
# Установка и настройка Redis как постоянной службы
# --------------------------------------------------------------
set -euo pipefail

echo "=== [1/4] Установка Redis ==="
apt-get update
apt-get install -y redis-server

echo "=== [2/4] Настройка Redis ==="
REDIS_CONF="/etc/redis/redis.conf"

# Резервная копия оригинального конфига
cp "$REDIS_CONF" "$REDIS_CONF.bak"

# Включаем постоянное сохранение на диск (RDB)
sed -i 's/^save ""/#save ""/' "$REDIS_CONF"
sed -i 's/^#save 900 1/save 900 1/' "$REDIS_CONF"
sed -i 's/^#save 300 10/save 300 10/' "$REDIS_CONF"
sed -i 's/^#save 60 10000/save 60 10000/' "$REDIS_CONF"

# Включаем AOF (дополнительная надёжность)
sed -i 's/^appendonly no/appendonly yes/' "$REDIS_CONF"

# Слушаем только localhost (безопасно)
sed -i 's/^bind 127.0.0.1 ::1/bind 127.0.0.1/' "$REDIS_CONF"

# Защищённый режим
sed -i 's/^protected-mode no/protected-mode yes/' "$REDIS_CONF"

echo "Конфигурация обновлена."

echo "=== [3/4] Запуск и автозапуск Redis ==="
systemctl start redis-server
systemctl enable redis-server

echo "=== [4/4] Проверка ==="
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis запущен и работает."
else
    echo "❌ Ошибка: Redis не запустился."
    systemctl status redis-server
    exit 1
fi

echo "----------------------------------------"
echo "ГОТОВО!"
echo ""
echo "Статус:       $(systemctl is-active redis-server)"
echo "Автозапуск:   $(systemctl is-enabled redis-server)"
echo "Порт:         6379 (только localhost)"
echo ""
echo "Проверить работу:"
echo "  redis-cli ping"
echo "  redis-cli SET mykey 'Hello Redis!'"
echo "  redis-cli GET mykey"
echo "----------------------------------------"
