#!/usr/bin/env python3
"""
Веб-версия AI-помощника Бусера. Мобильная + десктоп версия.
"""
from flask import Flask, request, jsonify
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
        return "Timeout (30s)"
    except Exception as e:
        return f"Error: {e}"

def collect_context():
    return f"""Time: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Uptime: {run_bash('uptime')}
Disk: {run_bash('df -h / | tail -1')}
Mem: {run_bash('free -h | grep Mem')}
Services: pg={run_bash('systemctl is-active postgresql')}, redis={run_bash('systemctl is-active redis-server')}, nginx={run_bash('systemctl is-active nginx')}
Top CPU: {run_bash('ps aux --sort=-%cpu --no-headers | head -3')}"""

SYSTEM_PROMPT = """You are Buser, a Linux server AI admin. Answer in Russian, short, friendly. 
Analyze server data and give advice. If you see errors, explain and suggest fixes."""

def ask_ai(context, question):
    full_prompt = f"Server context:\n{context}\n\nQuestion: {question}"
    
    # Пробуем разные модели
    models = ["gpt-4o-mini", "gpt-3.5-turbo", None]  # None = default
    
    for model in models:
        try:
            if model:
                response = g4f.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": full_prompt}
                    ]
                )
            else:
                response = g4f.ChatCompletion.create(
                    model=g4f.models.default,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": full_prompt}
                    ]
                )
            if response and len(response) > 10:
                return response
        except:
            continue
    
    return "AI temporarily unavailable. Try again or use quick commands (left panel)."

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Buser AI Admin</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{
            font-family:-apple-system,system-ui,sans-serif;
            background:#1a1a2e;color:#eee;
            min-height:100vh;min-height:100dvh;
        }
        
        /* ДЕСКТОП */
        @media(min-width:769px){
            body{display:flex}
            .sidebar{
                width:300px;min-width:300px;
                background:#16213e;padding:20px;
                border-right:1px solid #0f3460;
                display:flex;flex-direction:column;gap:15px;
                height:100vh;overflow-y:auto;
            }
            .main{flex:1;display:flex;flex-direction:column;padding:20px}
            .mobile-header{display:none}
            .mobile-tabs{display:none}
        }
        
        /* МОБИЛЬНАЯ */
        @media(max-width:768px){
            body{display:flex;flex-direction:column;height:100vh;height:100dvh}
            .sidebar{display:none}
            .sidebar.open{
                display:flex;flex-direction:column;
                position:fixed;top:0;left:0;width:100%;height:100%;
                background:#16213e;z-index:100;padding:20px;gap:15px;
                overflow-y:auto;
            }
            .mobile-header{
                display:flex;justify-content:space-between;align-items:center;
                padding:12px 16px;background:#16213e;
                border-bottom:1px solid #0f3460;
            }
            .mobile-header h2{color:#e94560;font-size:1.1em}
            .hamburger{
                background:none;border:none;color:#eee;font-size:1.5em;
                cursor:pointer;padding:5px;
            }
            .main{flex:1;display:flex;flex-direction:column;padding:10px;overflow:hidden}
            .chat{flex:1;overflow-y:auto;padding:5px}
            .mobile-tabs{
                display:flex;gap:5px;padding:8px;
                background:#16213e;overflow-x:auto;
            }
            .mobile-tabs button{
                flex-shrink:0;padding:8px 12px;border-radius:20px;
                border:1px solid #0f3460;background:transparent;
                color:#eee;font-size:.85em;cursor:pointer;
                white-space:nowrap;
            }
            .mobile-tabs button:active{background:#e94560}
        }
        
        h2{color:#e94560;font-size:1.3em}
        .quick-btn{
            background:#0f3460;color:#eee;border:none;
            padding:14px;border-radius:8px;cursor:pointer;
            text-align:left;font-size:.95em;width:100%;
            transition:background .2s;
        }
        .quick-btn:hover,.quick-btn:active{background:#1a5276}
        .chat{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
        .msg{
            max-width:85%;padding:12px 16px;border-radius:12px;
            line-height:1.5;word-wrap:break-word;white-space:pre-wrap;
            font-size:.95em;
        }
        .msg.user{align-self:flex-end;background:#0f3460}
        .msg.bot{align-self:flex-start;background:#16213e;border:1px solid #0f3460}
        .input-area{
            display:flex;gap:8px;padding:12px 0;
            border-top:1px solid #0f3460;
        }
        .input-area input{
            flex:1;padding:14px;border-radius:25px;
            border:1px solid #0f3460;background:#16213e;
            color:#eee;font-size:1em;outline:none;
        }
        .input-area input:focus{border-color:#e94560}
        .input-area button{
            width:50px;height:50px;border-radius:50%;
            border:none;background:#e94560;color:#fff;
            font-size:1.3em;cursor:pointer;flex-shrink:0;
            display:flex;align-items:center;justify-content:center;
        }
        .input-area button:active{background:#c73e54}
        .bash-area{margin-top:auto}
        .bash-area input{
            width:100%;padding:12px;border-radius:8px;
            border:1px solid #0f3460;background:#16213e;
            color:#eee;margin-bottom:8px;font-size:.9em;outline:none;
        }
        .bash-area input:focus{border-color:#e94560}
        .bash-area button{
            width:100%;padding:12px;border-radius:8px;
            border:none;background:#0f3460;color:#eee;
            cursor:pointer;font-size:.9em;
        }
        .status{font-size:.8em;color:#888;padding:8px}
        .close-btn{
            display:none;background:none;border:none;
            color:#e94560;font-size:1.5em;cursor:pointer;
        }
        @media(max-width:768px){.close-btn{display:block}}
    </style>
</head>
<body>
    <!-- Мобильный заголовок -->
    <div class="mobile-header">
        <h2>Buser</h2>
        <button class="hamburger" onclick="toggleSidebar()">☰</button>
    </div>
    
    <!-- Мобильные быстрые кнопки -->
    <div class="mobile-tabs">
        <button onclick="quick('status')">Status</button>
        <button onclick="quick('logs')">Logs</button>
        <button onclick="quick('memory')">Mem</button>
        <button onclick="quick('disk')">Disk</button>
        <button onclick="quick('processes')">CPU</button>
    </div>
    
    <!-- Сайдбар -->
    <div class="sidebar" id="sidebar">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <h2>Buser</h2>
            <button class="close-btn" onclick="toggleSidebar()">✕</button>
        </div>
        <div class="status" id="serverInfo">Loading...</div>
        <button class="quick-btn" onclick="quick('status')">Status</button>
        <button class="quick-btn" onclick="quick('logs')">PostgreSQL Logs</button>
        <button class="quick-btn" onclick="quick('memory')">Memory</button>
        <button class="quick-btn" onclick="quick('disk')">Disk</button>
        <button class="quick-btn" onclick="quick('processes')">Top Processes</button>
        <div class="bash-area">
            <input type="text" id="bashCmd" placeholder="bash command">
            <button onclick="bashExec()">Run Command</button>
        </div>
    </div>
    
    <!-- Основной чат -->
    <div class="main">
        <div class="chat" id="chat">
            <div class="msg bot">Hello! I'm Buser, your server AI admin.
            
Use left panel for quick checks or ask me anything about the server.</div>
        </div>
        <div class="input-area">
            <input type="text" id="msgInput" placeholder="Ask Buser..." 
                   onkeypress="if(event.key==='Enter')ask()">
            <button onclick="ask()">➤</button>
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

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

async function quick(cmd) {
    add(cmd, 'user');
    add('...', 'bot');
    // Закрываем сайдбар на мобилке
    document.getElementById('sidebar').classList.remove('open');
    try {
        const r = await fetch('/quick', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: cmd})
        });
        const data = await r.json();
        const msgs = chat.querySelectorAll('.msg.bot');
        msgs[msgs.length-1].textContent = data.result;
    } catch(e) {
        const msgs = chat.querySelectorAll('.msg.bot');
        msgs[msgs.length-1].textContent = 'Error';
    }
}

async function ask() {
    const inp = document.getElementById('msgInput');
    const text = inp.value.trim();
    if(!text) return;
    add(text, 'user');
    inp.value = '';
    add('...', 'bot');
    try {
        const r = await fetch('/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({question: text})
        });
        const data = await r.json();
        const msgs = chat.querySelectorAll('.msg.bot');
        msgs[msgs.length-1].textContent = data.answer;
    } catch(e) {
        const msgs = chat.querySelectorAll('.msg.bot');
        msgs[msgs.length-1].textContent = 'Error';
    }
}

async function bashExec() {
    const inp = document.getElementById('bashCmd');
    const cmd = inp.value.trim();
    if(!cmd) return;
    add('$ ' + cmd, 'user');
    inp.value = '';
    add('...', 'bot');
    try {
        const r = await fetch('/bash', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command: cmd})
        });
        const data = await r.json();
        const msgs = chat.querySelectorAll('.msg.bot');
        msgs[msgs.length-1].textContent = data.result;
    } catch(e) {
        const msgs = chat.querySelectorAll('.msg.bot');
        msgs[msgs.length-1].textContent = 'Error';
    }
}

// Загружаем hostname
fetch('/quick', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({command: 'hostname'})
}).then(r=>r.json()).then(d=>{
    document.getElementById('serverInfo').textContent = 'Host: '+d.result;
});
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
        "hostname": lambda: run_bash("hostname"),
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
