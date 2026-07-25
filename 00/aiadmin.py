#!/usr/bin/env python3
"""
AI-помощник по серверу.
Понимает команды, читает логи, объясняет ошибки.
Работает через g4f (без API-ключа).
"""
import subprocess
import os
import g4f
from datetime import datetime

# -------------------------------------------------------------
# ИНСТРУМЕНТЫ — что умеет помощник
# -------------------------------------------------------------
def check_service(service):
    """Проверить статус службы."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except:
        return "неизвестно"

def get_logs(service, lines=20):
    """Последние строки лога службы."""
    try:
        result = subprocess.run(
            ["journalctl", "-u", service, "--no-pager", "-n", str(lines)],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or "Логи пусты."
    except:
        return "Не удалось прочитать логи."

def get_disk():
    """Место на диске."""
    result = subprocess.run(
        ["df", "-h", "/"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def get_memory():
    """Оперативная память."""
    result = subprocess.run(
        ["free", "-h"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def get_processes():
    """Топ-5 процессов по CPU."""
    result = subprocess.run(
        ["ps", "aux", "--sort=-%cpu", "--no-headers"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")[:5]
    return "\n".join(lines)

def get_uptime():
    """Время работы сервера."""
    result = subprocess.run(["uptime"], capture_output=True, text=True)
    return result.stdout.strip()

def check_port(port):
    """Проверить, слушается ли порт."""
    result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True, text=True
    )
    if f":{port}" in result.stdout:
        return f"✅ Порт {port} прослушивается."
    return f"❌ Порт {port} не прослушивается."

# -------------------------------------------------------------
# AI-МОЗГ
# -------------------------------------------------------------
SYSTEM_PROMPT = """Ты — AI-администратор Linux-сервера.
Твоё имя — Бусер. Ты отвечаешь кратко, по-русски, дружелюбно.
Ты помогаешь диагностировать проблемы, читать логи и управлять сервером.
У тебя есть доступ к реальным данным сервера, которые тебе передаются.
Если видишь ошибки в логах — объясняешь их причину и предлагаешь решение.
Если всё хорошо — так и говоришь, без паники."""

def ask_ai(context, question):
    """Задать вопрос AI с контекстом о сервере."""
    full_prompt = f"""Контекст (реальные данные сервера):
{context}

Вопрос пользователя: {question}

Ответь кратко и по делу, опираясь на данные выше."""
    
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ]
        )
        return response
    except:
        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": full_prompt}
                ]
            )
            return response
        except Exception as e:
            return f"❌ AI недоступен: {e}"

# -------------------------------------------------------------
# СБОР ДАННЫХ О СЕРВЕРЕ
# -------------------------------------------------------------
def collect_context():
    """Собрать сводку о состоянии сервера."""
    return f"""Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Аптайм: {get_uptime()}

Диск:
{get_disk()}

Память:
{get_memory()}

Статусы служб:
  postgresql: {check_service('postgresql')}
  redis-server: {check_service('redis-server')}
  ssh: {check_service('ssh')}
  nginx: {check_service('nginx')}

Порты:
  SSH (1965): {'✅' if '1965' in subprocess.run(['ss','-tlnp'], capture_output=True, text=True).stdout else '❌'}
  PostgreSQL (5432): {'✅' if '5432' in subprocess.run(['ss','-tlnp'], capture_output=True, text=True).stdout else '❌'}
  Redis (6379): {'✅' if '6379' in subprocess.run(['ss','-tlnp'], capture_output=True, text=True).stdout else '❌'}

Топ-5 процессов:
{get_processes()}"""

# -------------------------------------------------------------
# КОМАНДЫ
# -------------------------------------------------------------
COMMANDS = {
    "статус": lambda: collect_context(),
    "логи": lambda: get_logs("postgresql"),
    "логи nginx": lambda: get_logs("nginx"),
    "логи ssh": lambda: get_logs("ssh"),
    "диск": get_disk,
    "память": get_memory,
    "процессы": get_processes,
    "аптайм": get_uptime,
}

def execute_command(cmd):
    """Выполнить встроенную команду."""
    cmd = cmd.lower().strip()
    if cmd in COMMANDS:
        return COMMANDS[cmd]()
    elif cmd.startswith("логи "):
        service = cmd.replace("логи ", "").strip()
        return get_logs(service)
    elif cmd.startswith("порт "):
        port = cmd.replace("порт ", "").strip()
        return check_port(port)
    return None

# -------------------------------------------------------------
# ГЛАВНЫЙ ЦИКЛ
# -------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("  🤖 БУСЕР — AI-помощник по серверу")
    print("=" * 55)
    print("  статус      — сводка о сервере")
    print("  логи        — последние логи PostgreSQL")
    print("  логи nginx  — логи веб-сервера")
    print("  память      — использование RAM")
    print("  диск        — свободное место")
    print("  порт 5432   — проверка порта")
    print("  <вопрос>    — спросить AI о сервере")
    print("  exit        — выход")
    print("=" * 55)

    while True:
        try:
            user_input = input("\n🔧 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Пока!")
            break

        if user_input.lower() == "exit":
            print("👋 Сервер под присмотром. Пока!")
            break

        if not v:
            continue

        # Сначала проверяем встроенные команды
        cmd_result = execute_command(user_input)
        if cmd_result:
            print(f"\n📊 Результат:\n{cmd_result}")
            continue

        # Иначе — спрашиваем AI
        print("🤖 Думаю...", end="", flush=True)
        context = collect_context()
        answer = ask_ai(context, user_input)
        print(f"\r🤖 {answer}\n")
