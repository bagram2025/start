#!/usr/bin/env python3
"""
Главная страница-портал сервера.
"""
from flask import Flask
import subprocess

app = Flask(__name__)

def run_bash(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except:
        return "—"

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Сервер Бусера</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{
            font-family:-apple-system,system-ui,sans-serif;
            background:#1a1a2e;color:#eee;
            min-height:100vh;
            display:flex;flex-direction:column;align-items:center;
            padding:20px;
        }
        .container{max-width:800px;width:100%}
        h1{
            text-align:center;color:#e94560;
            font-size:2em;margin:30px 0 10px;
        }
        .subtitle{
            text-align:center;color:#888;margin-bottom:40px;
            font-size:1.1em;
        }
        .cards{
            display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
            gap:20px;
        }
        .card{
            background:#16213e;border:1px solid #0f3460;
            border-radius:16px;padding:30px 20px;
            text-align:center;text-decoration:none;
            transition:transform .2s,box-shadow .2s;
            display:flex;flex-direction:column;
            align-items:center;gap:15px;
        }
        .card:hover{
            transform:translateY(-4px);
            box-shadow:0 8px 25px rgba(233,69,96,.2);
            border-color:#e94560;
        }
        .card-icon{font-size:3em}
        .card-title{color:#eee;font-size:1.2em;font-weight:bold}
        .card-desc{color:#888;font-size:.9em;line-height:1.4}
        .status-bar{
            background:#16213e;border-radius:12px;
            padding:20px;margin-top:40px;
            display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
            gap:15px;text-align:center;
        }
        .stat-value{color:#e94560;font-size:1.3em;font-weight:bold}
        .stat-label{color:#888;font-size:.8em;margin-top:4px}
        .footer{
            text-align:center;color:#555;margin-top:40px;
            font-size:.85em;
        }
        @media(max-width:500px){
            h1{font-size:1.5em}
            .cards{grid-template-columns:1fr}
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Сервер Бусера</h1>
        <div class="subtitle">Персональный VPS с AI-администратором</div>
        
        <div class="cards">
            <a href="/admin" class="card">
                <div class="card-icon">🤖</div>
                <div class="card-title">AI-Администратор</div>
                <div class="card-desc">Чат с Бусером: статус сервера, логи, диагностика, bash-команды</div>
            </a>
            
            <a href="/panel" class="card">
                <div class="card-icon">📊</div>
                <div class="card-title">Админ-панель</div>
                <div class="card-desc">Статистика сервера: CPU, память, диск, процессы в реальном времени</div>
            </a>
            
            <a href="/diary" class="card">
                <div class="card-icon">📓</div>
                <div class="card-title">Дневник</div>
                <div class="card-desc">Терминальный дневник с хранением в PostgreSQL</div>
            </a>
            
            <a href="/redis" class="card">
                <div class="card-icon">⚡</div>
                <div class="card-title">Redis-демо</div>
                <div class="card-desc">Тест-драйв Redis: кэширование, рейтинги, очереди</div>
            </a>
        </div>
        
        <div class="status-bar">
            <div>
                <div class="stat-value" id="uptime">—</div>
                <div class="stat-label">Аптайм</div>
            </div>
            <div>
                <div class="stat-value" id="disk">—</div>
                <div class="stat-label">Диск</div>
            </div>
            <div>
                <div class="stat-value" id="mem">—</div>
                <div class="stat-label">Память</div>
            </div>
            <div>
                <div class="stat-value" id="cpu">—</div>
                <div class="stat-label">CPU</div>
            </div>
        </div>
        
        <div class="footer">
            Buser Server • {{ hostname }} • {{ ip }}
        </div>
    </div>
    
    <script>
        async function loadStats() {
            try {
                const r = await fetch('/stats');
                const d = await r.json();
                document.getElementById('uptime').textContent = d.uptime;
                document.getElementById('disk').textContent = d.disk;
                document.getElementById('mem').textContent = d.mem;
                document.getElementById('cpu').textContent = d.cpu;
            } catch(e) {}
        }
        loadStats();
        setInterval(loadStats, 30000);
    </script>
</body>
</html>"""

@app.route("/")
def index():
    hostname = run_bash("hostname")
    ip = run_bash("hostname -I | awk '{print $1}'")
    return HTML.replace("{{ hostname }}", hostname).replace("{{ ip }}", ip)

@app.route("/stats")
def stats():
    uptime = run_bash("uptime -p | sed 's/up //'")
    disk = run_bash("df -h / | tail -1 | awk '{print $5}'")
    mem = run_bash("free -h | grep Mem | awk '{print $3 \"/\" $2}'")
    cpu = run_bash("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'") + "%"
    return {
        "uptime": uptime or "—",
        "disk": disk or "—",
        "mem": mem or "—",
        "cpu": cpu or "—"
    }

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
