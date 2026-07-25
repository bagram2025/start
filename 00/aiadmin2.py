#!/usr/bin/env python3
"""
AI-помощник по серверу с выполнением bash-команд.
Понимает команды, читает логи, объясняет ошибки, выполняет bash.
Работает через g4f (без API-ключа).
"""
import subprocess
import os
import g4f
from datetime import datetime

# -------------------------------------------------------------
# ИНСТРУМЕНТЫ — что умеет помощник
# -------------------------------------------------------------
def run_bash(command):
    """Выполнить bash-команду и вернуть результат."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if error:
            return f"{output}\n{error}".strip()
        return output or "(команда выполнена, нет вывода)"
    except subprocess.TimeoutExpired:
        return "⏰ Команда выполнялась больше 30 секунд и была прервана."
    except Exception as e:
        return f"❌ Ошибка: {e}"

def check_service(service):
    """Проверить статус службы."""
    return run_bash(f"systemctl is-active {service}")

def get_logs(service, lines=20):
    """Последние строки лога службы."""
    return run_bash(f"journalctl -u {service} --no-pager -n {lines}")

def get_disk():
    """Место на диске."""
    return run_bash("df -h /")

def get_memory():
    """Оперативная память."""
    return run_bash("free -h")

def get_processes():
    """Топ-5 процессов по CPU."""
    return run_bash("ps aux --sort=-%cpu --no-headers | head -5")

def get_uptime():
    """Время работы сервера."""
    return run_bash("uptime")

def check_port(port):
    """Проверить, слушается ли порт."""
    return run_bash(f"ss -tlnp | grep ':{port}' || echo '❌ Порт {port} не прослушивается.'")

def get_ssh_attempts():
    """Попытки входа по SSH (последние 10)."""
    return run_bash("journalctl -u ssh --no-pager -n 10 2>/dev/null || echo 'Логи SSH не найдены.'")

# -------------------------------------------------------------
# AI-МОЗГ
# -------------------------------------------------------------
SYSTEM_PROMPT = """Ты — AI-администратор Linux-сервера.
Твоё имя — Бусер. Ты отвечаешь кратко, по-русски, дружелюбно.
Ты помогаешь диагностировать проблемы, читать логи и управлять сервером.
У тебя есть доступ к реальным данным сервера, которые тебе передаются.
Если видишь ошибки в логах — объясняешь их причину и предлагаешь решение.
Если всё хорошо — так и говоришь, без паники.
Ты можешь предлагать пользователю выполнить bash-команды, 
но сам их не выполняешь — для этого есть команда ! (восклицательный знак)."""

def ask_ai(context, question):
    """Задать вопрос AI с контекстом о сервере."""
    full_prompt = f"""Контекст (реальные данные сервера):
{context}

Вопрос пользователя: {question}

Ответь кратко и по делу, опираясь на данные выше.
Если для решения нужна bash-команда, предложи её пользователю в формате: 
"Выполни: !команда"
"""
    
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
    # Быстрый сбор без тяжёлых запросов
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

Топ-5 процессов:
{get_processes()}"""

# -------------------------------------------------------------
# КОМАНДЫ
# -------------------------------------------------------------
COMMANDS = {
    "статус": collect_context,
    "логи": lambda: get_logs("postgresql"),
    "логи nginx": lambda: get_logs("nginx"),
    "логи ssh": get_ssh_attempts,
    "логи redis": lambda: get_logs("redis-server"),
    "диск": get_disk,
    "память": get_memory,
    "процессы": get_processes,
    "аптайм": get_uptime,
    "help": lambda: """Доступные команды:
  статус        — полная сводка о сервере
  логи          — последние логи PostgreSQL
  логи nginx    — логи веб-сервера
  логи ssh      — попытки входа по SSH
  логи redis    — логи Redis
  память        — использование RAM
  диск          — свободное место
  процессы      — топ-5 процессов по CPU
  порт <число>  — проверка порта
  !<команда>    — выполнить bash-команду
  <вопрос>      — спросить AI о сервере
  exit          — выход""",
}

def execute_command(cmd):
    """Выполнить встроенную команду или bash."""
    cmd = cmd.strip()
    
    # Bash-команда через !
    if cmd.startswith("!"):
        bash_cmd = cmd[1:].strip()
        if bash_cmd:
            print(f"⚡ Выполняю: {bash_cmd}")
            return run_bash(bash_cmd)
        return "Укажите команду после !"
    
    cmd_lower = cmd.lower()
    
    # Встроенные команды
    if cmd_lower in COMMANDS:
        return COMMANDS[cmd_lower]()
    
    # Проверка порта
    if cmd_lower.startswith("порт "):
        port = cmd_lower.replace("порт ", "").strip()
        return check_port(port)
    
    # Логи произвольной службы
    if cmd_lower.startswith("логи "):
        service = cmd_lower.replace("логи ", "").strip()
        if service not in ("nginx", "ssh", "redis"):
            return get_logs(service)
    
    return None

# -------------------------------------------------------------
# ГЛАВНЫЙ ЦИКЛ
# -------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("  🤖 БУСЕР — AI-помощник по серверу")
    print("=" * 55)
    print("  статус         — сводка о сервере")
    print("  логи / память  — системная информация")
    print("  !команда       — выполнить bash (пример: !ls -la)")
    print("  <вопрос>       — спросить AI о сервере")
    print("  help           — все команды")
    print("  exit           — выход")
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

        if not user_input:
            continue

        # Сначала проверяем встроенные команды и bash
        cmd_result = execute_command(user_input)
        if cmd_result is not None:
            print(f"\n📊 Результат:\n{cmd_result}")
            continue

        # Иначе — спрашиваем AI
        print("🤖 Думаю...", end="", flush=True)
        context = collect_context()
        answer = ask_ai(context, user_input)
        print(f"\r🤖 {answer}\n")
