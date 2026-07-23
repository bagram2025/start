#!/usr/bin/env python3
"""
Демонстрация возможностей Redis.
Каждый тест можно запускать отдельно.
"""
import redis
import time

# Подключение
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def sep(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

# -------------------------------------------------------------
# 1. СТРОКИ — основа всего
# -------------------------------------------------------------
def test_strings():
    sep("1. СТРОКИ (Strings)")

    r.set("hero", "Бусер")
    print(f"SET hero → {r.get('hero')}")

    # Строка с автоудалением через 10 секунд
    r.setex("temp", 10, "Исчезну через 10 секунд")
    print(f"SETEX temp → {r.get('temp')}")
    print(f"TTL temp → {r.ttl('temp')} сек")

    # Увеличить счётчик
    r.set("visits", 0)
    r.incr("visits")
    r.incr("visits", 5)
    print(f"INCR visits → {r.get('visits')}")

# -------------------------------------------------------------
# 2. ХЭШИ — объекты с полями
# -------------------------------------------------------------
def test_hashes():
    sep("2. ХЭШИ (Hashes)")

    r.hset("user:1", mapping={
        "name": "Бусер",
        "role": "admin",
        "server": "p665038",
    })
    print(f"HGETALL user:1 → {r.hgetall('user:1')}")
    print(f"HGET user:1 name → {r.hget('user:1', 'name')}")

# -------------------------------------------------------------
# 3. СПИСКИ — очереди и логи
# -------------------------------------------------------------
def test_lists():
    sep("3. СПИСКИ (Lists)")

    r.delete("log")
    r.rpush("log", "Сервер запущен")
    r.rpush("log", "Redis подключён")
    r.rpush("log", "Демо запущено")
    print(f"LRANGE log 0 -1 → {r.lrange('log', 0, -1)}")
    print(f"LPOP log → {r.lpop('log')} (извлечён первый элемент)")
    print(f"Осталось → {r.lrange('log', 0, -1)}")

# -------------------------------------------------------------
# 4. МНОЖЕСТВА — уникальные значения
# -------------------------------------------------------------
def test_sets():
    sep("4. МНОЖЕСТВА (Sets)")

    r.delete("tags:redis")
    r.sadd("tags:redis", "быстрый", "в памяти", "NoSQL", "кэш")
    print(f"SMEMBERS tags:redis → {r.smembers('tags:redis')}")

    # Проверка на вхождение
    print(f"SISMEMBER 'быстрый' → {r.sismember('tags:redis', 'быстрый')}")
    print(f"SISMEMBER 'тормоз' → {r.sismember('tags:redis', 'тормоз')}")

# -------------------------------------------------------------
# 5. ОТСОРТИРОВАННЫЕ МНОЖЕСТВА — рейтинги
# -------------------------------------------------------------
def test_sorted_sets():
    sep("5. ОТСОРТИРОВАННЫЕ МНОЖЕСТВА (Sorted Sets)")

    r.delete("rating")
    r.zadd("rating", {"Бусер": 100, "Redis": 95, "Python": 90, "PostgreSQL": 85})
    print("Топ-3:")
    for name, score in r.zrevrange("rating", 0, 2, withscores=True):
        print(f"  {name}: {int(score)} баллов")

    # На сколько Redis круче PostgreSQL?
    redis_score = r.zscore("rating", "Redis")
    pg_score = r.zscore("rating", "PostgreSQL")
    print(f"\nRedis круче PostgreSQL на {int(redis_score - pg_score)} баллов")

# -------------------------------------------------------------
# 6. КЭШИРОВАНИЕ — главная красота
# -------------------------------------------------------------
def test_cache():
    sep("6. КЭШИРОВАНИЕ (главная фишка)")

    def тяжёлый_запрос():
        """Типа ходим в PostgreSQL — это долго (2 секунды)"""
        time.sleep(2)
        return "Данные из PostgreSQL"

    def умный_запрос():
        """Сначала смотрим в Redis"""
        cached = r.get("pg_result")
        if cached:
            print("  ⚡ МОЛНИЯ! Взято из кэша Redis")
            return cached
        print("  🐢 Идём в PostgreSQL...")
        result = тяжёлый_запрос()
        r.setex("pg_result", 5, result)  # кэш на 5 секунд
        return result

    # Первый вызов — медленный
    t1 = time.time()
    print(f"  Запрос 1: {умной_запрос()}")
    print(f"  Время: {time.time() - t1:.2f} сек\n")

    # Второй вызов — из кэша
    t2 = time.time()
    print(f"  Запрос 2: {умной_запрос()}")
    print(f"  Время: {time.time() - t2:.4f} сек")

# -------------------------------------------------------------
# ЗАПУСК ВСЕХ ТЕСТОВ
# -------------------------------------------------------------
if __name__ == "__main__":
    try:
        r.ping()
        print("✅ Redis подключён. Начинаем демонстрацию...")
    except redis.ConnectionError:
        print("❌ Redis не доступен. Запустите redis-server.")
        exit(1)

    test_strings()
    test_hashes()
    test_lists()
    test_sets()
    test_sorted_sets()
    test_cache()

    sep("ИТОГ")
    print("Redis — это не просто key:value.")
    print("Это структуры данных, живущие в оперативной памяти.")
    print("Быстро, красиво, надёжно.")
    print(f"\nВсе ключи этого демо: {r.keys('*')}")
