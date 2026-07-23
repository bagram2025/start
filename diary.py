#!/usr/bin/env python3
"""
Терминальный дневник.
Запуск: python3 diary.py
Команды: write, read, exit
"""
import os
import psycopg2
from datetime import datetime
from getpass import getuser

# ---------- НАСТРОЙКИ (измените под себя) ----------
DB_NAME = "test"
DB_USER = "test"
DB_PASS = "test"
DB_HOST = "localhost"
# --------------------------------------------------

def get_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
    )

def init():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS diary (
            id SERIAL PRIMARY KEY,
            entry TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def write():
    print("\n✍️  Пишите (Enter — новая строка, пустая строка + Enter — сохранить):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    text = "\n".join(lines)
    if text.strip():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO diary (entry) VALUES (%s)", (text,))
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Сохранено!\n")
    else:
        print("❌ Пусто. Ничего не сохранено.\n")

def read():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, entry, created_at FROM diary ORDER BY id DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("\n📭 Дневник пуст.\n")
        return

    print("\n📖 Последние записи:\n")
    for row_id, entry, date in reversed(rows):
        print(f"#{row_id} | {date.strftime('%d.%m.%Y %H:%M')}")
        print("-" * 40)
        print(entry)
        print("-" * 40)
        print()

def main():
    init()
    print("=" * 40)
    print("📓 ДНЕВНИК")
    print("=" * 40)
    while True:
        cmd = input("write / read / exit > ").strip().lower()
        if cmd == "write":
            write()
        elif cmd == "read":
            read()
        elif cmd == "exit":
            print("👋 Пока!")
            break
        else:
            print("Неизвестная команда. Доступны: write, read, exit\n")

if __name__ == "__main__":
    main()
