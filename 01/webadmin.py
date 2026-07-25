#!/usr/bin/env python3
"""
Веб-версия AI-помощника Бусера.
"""
from flask import Flask, render_template_string, request, jsonify
import subprocess
import g4f
from datetime import datetime

app = Flask(__name__)

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
        return "Timeout"
    except Exception as e:
        return f"Error: {e}"

def collect_context():
    return f"""Time: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Uptime: {run_bash('uptime')}
Disk: {run_bash('df -h / | tail -1')}
Mem: {run_bash('free -h | grep Mem')}
Services: pg={run_bash('systemctl is-active postgresql')}, redis={run_bash('systemctl is-active redis-server')}, nginx={run_bash('systemctl is-active nginx')}
Top CPU: {run_bash('ps aux --sort=-%cpu --no-headers | head -3')}"""

SYSTEM_PROMPT = """You are Buser, a Linux server AI admin. Answer in Russian, short, friendly."""

def ask_ai(context, question):
    full_prompt = f"Server context:\n{context}\n\nQuestion: {question}"
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt}
            ]
        )
        return response
    except Exception as e:
        return f"AI error: {e}"

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buser AI Admin</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,system-ui,sans-serif;background:#1a1a2e;color:#eee;min-height:100vh;display:flex}
        .sidebar{width:300px;background:#16213e;padding:20px;border-right:1px solid #0f3460;display:flex;flex-direction:column;gap:15px}
        .sidebar h2{color:#e94560;font-size:1.3em}
        .quick-btn{background:#0f3460;color:#eee;border:none;padding:12px;border-radius:8px;cursor:pointer;text-align:left;font-size:.95em}
        .quick-btn:hover{background:#1a5276}
        .main{flex:1;display:flex;flex-direction:column;padding:20px}
        .chat{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:15px;padding:10px}
        .msg{max-width:80%;padding:12px 16px;border-radius:12px;line-height:1.5;white-space:pre-wrap}
        .msg.user{align-self:flex-end;background:#0f3460}
        .msg.bot{align-self:flex-start;background:#16213e;border:1px solid #0f3460}
        .input-area{display:flex;gap:10px;padding:15px 0;border-top:1px solid #0f3460}
        .input-area input{flex:1;padding:14px;border-radius:10px;border:1px solid #0f3460;background:#16213e;color:#eee;font-size:1em}
        .input-area button{padding:14px 25px;border-radius:10px;border:none;background:#e94560;color:#fff;font-size:1em;cursor:pointer;font-weight:bold}
        .bash-area{margin-top:auto}
        .bash-area input{width:100%;padding:10px;border-radius:6px;border:1px solid #0f3460;background:#16213e;color:#eee;margin-bottom:8px}
        .bash-area button{width:100%;padding:10px;border-radius:6px;border:none;background:#0f3460;color:#eee;cursor:pointer}
        .status{font-size:.85em;color:#888;padding:10px}
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>Buser</h2>
        <div class="status" id="serverInfo">Server</div>
        <button class="quick-btn" onclick="quick('status')">Status</button>
        <button class="quick-btn" onclick="quick('logs')">Logs PG</button>
        <button class="quick-btn" onclick="quick('memory')">Memory</button>
        <button class="quick-btn" onclick="quick('disk')">Disk</button>
        <button class="quick-btn" onclick="quick('processes')">Processes</button>
        <div class="bash-area">
            <input type="text" id="bashCmd" placeholder="bash command">
            <button onclick="bashExec()">Run</button>
        </div>
    </div>
    <div class="main">
        <div class="chat" id="chat"></div>
        <div class="input-area">
            <input type="text" id="msgInput" placeholder="Ask Buser..." onkeypress="if(event.key==='Enter')ask()">
            <button onclick="ask()">Send</button>
        </div>
    </div>
<script>
const chat = document.getElementById('chat');

function add(msg, cls) {
    const d = document.createElement('div');
    d.className = 'msg ' + cls;
    d.textContent = msg;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
}

async function quick(cmd) {
    add(cmd, 'user');
    add('Running...', 'bot');
    try {
        const r = await fetch('/quick', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: cmd})
        });
        const data = await r.json();
        const last = chat.querySelectorAll('.msg.bot');
        last[last.length-1].textContent = data.result;
    } catch(e) {
        const last = chat.querySelectorAll('.msg.bot');
        last[last.length-1].textContent = 'Connection error';
    }
}

async function ask() {
    const inp = document.getElementById('msgInput');
    const text = inp.value.trim();
    if(!text) return;
    add(text, 'user');
    inp.value = '';
    add('Thinking...', 'bot');
    try {
        const r = await fetch('/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: text})
        });
        const data = await r.json();
        const last = chat.querySelectorAll('.msg.bot');
        last[last.length-1].textContent = data.answer;
    } catch(e) {
        const last = chat.querySelectorAll('.msg.bot');
        last[last.length-1].textContent = 'Connection error';
    }
}

async function bashExec() {
    const inp = document.getElementById('bashCmd');
    const cmd = inp.value.trim();
    if(!cmd) return;
    add('$ ' + cmd, 'user');
    inp.value = '';
    add('Running...', 'bot');
    try {
        const r = await fetch('/bash', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: cmd})
        });
        const data = await r.json();
        const last = chat.querySelectorAll('.msg.bot');
        last[last.length-1].textContent = data.result;
    } catch(e) {
        const last = chat.querySelectorAll('.msg.bot');
        last[last.length-1].textContent = 'Error';
    }
}
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "")
    context = collect_context()
    answer = ask_ai(context, question)
    return jsonify({"answer": answer})

@app.route("/quick", methods=["POST"])
def quick():
    data = request.get_json()
    cmd = data.get("command", "")
    commands = {
        "status": collect_context,
        "logs": lambda: run_bash("journalctl -u postgresql --no-pager -n 20"),
        "memory": lambda: run_bash("free -h"),
        "disk": lambda: run_bash("df -h /"),
        "processes": lambda: run_bash("ps aux --sort=-%cpu --no-headers | head -5"),
    }
    result = commands.get(cmd, lambda: f"Unknown: {cmd}")()
    return jsonify({"result": result})

@app.route("/bash", methods=["POST"])
def bash():
    data = request.get_json()
    command = data.get("command", "")
    result = run_bash(command)
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
