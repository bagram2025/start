#!/usr/bin/env python3
"""
Веб-версия AI-помощника Бусера.
"""
from flask import Flask, render_template_string, request, jsonify
import subprocess
import g4f
from datetime import datetime

app = Flask(__name__)

# -------------------------------------------------------------
# ИНСТРУМЕНТЫ (те же, что в консольной версии)
# -------------------------------------------------------------
def run_bash(command):
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if error:
            return f"{output}\n{error}".strip()
        return output or "OK"
    except subprocess.TimeoutExpired:
        return "⏰ Прервано (30 сек)."
    except Exception as e:
        return f"❌ Ошибка: {e}"

def collect_context():
    return f"""Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Аптайм: {run_bash('uptime')}
Диск: {run_bash('df -h / | tail -1')}
Память: {run_bash('free -h | grep Mem')}
Статусы: postgresql={run_bash('systemctl is-active postgresql')}, redis={run_bash('systemctl is-active redis-server')}, nginx={run_bash('systemctl is-active nginx')}
Топ CPU: {run_bash('ps aux --sort=-%cpu --no-headers | head -3')}"""

SYSTEM_PROMPT = """Ты — Бусер, AI-администратор Linux-сервера.
Отвечай кратко, по-русски, дружелюбно.
Анализируй данные сервера и предлагай решения.
Если нужна bash-команда, пиши: "Выполни: !команда".
Пользователь выполнит её и пришлёт результат."""

def ask_ai(context, question):
    full_prompt = f"""Контекст сервера:
{context}

Вопрос: {question}"""
    
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
# МАРШРУТЫ
# -------------------------------------------------------------
HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Бусер — AI-администратор</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, system-ui, sans-serif;
            background: #1a1a2e; color: #eee;
            min-height: 100vh;
            display: flex;
        }
        .sidebar {
            width: 300px; background: #16213e; padding: 20px;
            border-right: 1px solid #0f3460;
            display: flex; flex-direction: column;
            gap: 15px;
        }
        .sidebar h2 { color: #e94560; font-size: 1.3em; }
        .quick-btn {
            background: #0f3460; color: #eee; border: none;
            padding: 12px; border-radius: 8px; cursor: pointer;
            text-align: left; font-size: 0.95em;
            transition: background 0.2s;
        }
        .quick-btn:hover { background: #1a5276; }
        .main {
            flex: 1; display: flex; flex-direction: column;
            padding: 20px;
        }
        .chat {
            flex: 1; overflow-y: auto;
            display: flex; flex-direction: column; gap: 15px;
            padding: 10px;
        }
        .msg {
            max-width: 80%; padding: 12px 16px;
            border-radius: 12px; line-height: 1.5;
        }
        .msg.user { align-self: flex-end; background: #0f3460; }
        .msg.bot { align-self: flex-start; background: #16213e; border: 1px solid #0f3460; }
        .msg pre { background: #1a1a2e; padding: 10px; border-radius: 6px; overflow-x: auto; margin: 8px 0; font-size: 0.9em; }
        .input-area {
            display: flex; gap: 10px; padding: 15px 0;
            border-top: 1px solid #0f3460;
        }
        .input-area input {
            flex: 1; padding: 14px; border-radius: 10px;
            border: 1px solid #0f3460; background: #16213e;
            color: #eee; font-size: 1em;
        }
        .input-area button {
            padding: 14px 25px; border-radius: 10px;
            border: none; background: #e94560; color: white;
            font-size: 1em; cursor: pointer; font-weight: bold;
        }
        .input-area button:hover { background: #c73e54; }
        .status { font-size: 0.85em; color: #888; padding: 10px; }
        .result-block { background: #1a1a2e; padding: 10px; border-radius: 6px; margin: 5px 0; white-space: pre-wrap; font-family: monospace; font-size: 0.85em; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🤖 Бусер</h2>
        <div class="status">Сервер: {{ hostname }}</div>
        <button class="quick-btn" onclick="sendQuick('статус')">📊 Статус сервера</button>
        <button class="quick-btn" onclick="sendQuick('логи')">📋 Логи PostgreSQL</button>
        <button class="quick-btn" onclick="sendQuick('память')">🧠 Память</button>
        <button class="quick-btn" onclick="sendQuick('диск')">💾 Диск</button>
        <button class="quick-btn" onclick="sendQuick('процессы')">⚡ Процессы</button>
        <button class="quick-btn" onclick="sendQuick('логи nginx')">🌐 Логи Nginx</button>
        <div class="status" style="margin-top: auto;">
            <input type="text" id="bashInput" placeholder="!команда" 
                   style="width:100%;padding:10px;border-radius:6px;border:1px solid #0f3460;background:#16213e;color:#eee;">
            <button onclick="sendBash()" style="width:100%;margin-top:8px;padding:10px;border-radius:6px;border:none;background:#0f3460;color:#eee;cursor:pointer;">⚙ Выполнить</button>
        </div>
    </div>
    <div class="main">
        <div class="chat" id="chat"></div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Спроси Бусера о сервере..." 
                   onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">➤</button>
        </div>
    </div>

    <script>
        function addMsg(text, type) {
            const chat = document.getElementById('chat');
            const div = document.createElement('div');
            div.className = `msg ${type}`;
            div.innerHTML = text.replace(/\n/g, '<br>');
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;
            addMsg(text, 'user');
            input.value = '';
            
            addMsg('🤔 Думаю...', 'bot');
            
            try {
                const resp = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: text})
                });
                const data = await resp.json();
                document.querySelector('#chat .msg.bot:last-child').innerHTML = 
                    data.answer.replace(/\n/g, '<br>');
            } catch(e) {
                document.querySelector('#chat .msg.bot:last-child').innerHTML = 
                    '❌ Ошибка соединения';
            }
        }

        async function sendQuick(cmd) {
            addMsg(cmd, 'user');
            addMsg('⏳ Выполняю...', 'bot');
            try {
                const resp = await fetch('/quick', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: cmd})
                });
                const data = await resp.json();
                document.querySelector('#chat .msg.bot:last-child').innerHTML = 
                    `<div class="result-block">${data.result}</div>`;
            } catch(e) {
                document.querySelector('#chat .msg.bot:last-child').innerHTML = 
                    '❌ Ошибка';
            }
        }

        async function sendBash() {
            const input = document.getElementById('bashInput');
            const cmd = input.value.trim();
            if (!cmd) return;
            addMsg('!' + cmd, 'user');
            addMsg('⏳ Выполняю...', 'bot');
            try {
                const resp = await fetch('/bash', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: cmd})
                });
                const data = await resp.json();
                document.querySelector('#chat .msg.bot:last-child').innerHTML = 
                    `<div class="result-block">${data.result}</div>`;
            } catch(e) {
                document.querySelector('#chat .msg.bot:last-child').innerHTML = 
                    '❌ Ошибка';
            }
            input.value = '';
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    hostname = run_bash("hostname")
    return render_template_string(HTML, hostname=hostname)

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question", "")
    context = collect_context()
    answer = ask_ai(context, question)
    return jsonify({"answer": answer})

@app.route("/quick", methods=["POST"])
def quick():
    cmd = request.json.get("command", "")
    # Те же команды, что в консольной версии
    commands = {
        "статус": collect_context,
        "логи": lambda: run_bash("journalctl -u postgresql --no-pager -n 20"),
        "логи nginx": lambda: run_bash("journalctl -u nginx --no-pager -n 20"),
        "память": lambda: run_bash("free -h"),
        "диск": lambda: run_bash("df -h /"),
        "процессы": lambda: run_bash("ps aux --sort=-%cpu --no-headers | head -5"),
    }
    result = commands.get(cmd, lambda: f"Неизвестная команда: {cmd}")()
    return jsonify({"result": result})

@app.route("/bash", methods=["POST"])
def bash():
    command = request.json.get("command", "")
    result = run_bash(command)
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
