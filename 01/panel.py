#!/usr/bin/env python3
"""
Админ-панель сервера. Статистика, графики, управление службами.
"""
from flask import Flask, jsonify
import subprocess
from datetime import datetime

app = Flask(__name__)

def run_bash(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return "—"

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ-панель</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{
            font-family:-apple-system,system-ui,sans-serif;
            background:#1a1a2e;color:#eee;min-height:100vh;
            padding:20px;
        }
        .container{max-width:900px;margin:0 auto}
        .header{
            display:flex;justify-content:space-between;align-items:center;
            margin-bottom:30px;flex-wrap:wrap;gap:15px;
        }
        h1{color:#e94560;font-size:1.8em}
        .back-btn{
            color:#eee;text-decoration:none;background:#0f3460;
            padding:10px 20px;border-radius:8px;font-size:.9em;
        }
        .back-btn:hover{background:#1a5276}
        
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:30px}
        .card{
            background:#16213e;border:1px solid #0f3460;
            border-radius:12px;padding:20px;
        }
        .card-value{font-size:2em;font-weight:bold;color:#e94560;margin-bottom:5px}
        .card-label{color:#888;font-size:.85em}
        
        .section{margin-bottom:30px}
        .section-title{
            color:#eee;font-size:1.2em;margin-bottom:15px;
            padding-bottom:10px;border-bottom:1px solid #0f3460;
        }
        
        table{width:100%;border-collapse:collapse}
        th,td{padding:12px;text-align:left;border-bottom:1px solid #0f3460}
        th{color:#888;font-size:.85em}
        td{font-size:.9em}
        
        .service-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #0f3460}
        .service-name{font-weight:bold}
        .service-status{padding:4px 12px;border-radius:20px;font-size:.85em}
        .status-active{background:#1a3a1a;color:#66bb6a}
        .status-inactive{background:#3a1a1a;color:#e94560}
        
        .refresh{color:#888;font-size:.8em;text-align:center;margin-top:20px}
        
        .chart-bar{
            height:8px;background:#0f3460;border-radius:4px;
            margin-top:5px;overflow:hidden;
        }
        .chart-fill{
            height:100%;border-radius:4px;transition:width 1s;
        }
        .fill-green{background:#4caf50}.fill-yellow{background:#ff9800}.fill-red{background:#e94560}
        
        @media(max-width:600px){
            h1{font-size:1.3em}
            .card-value{font-size:1.5em}
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Админ-панель</h1>
            <a href="/" class="back-btn">← На главную</a>
        </div>
        
        <!-- Основные метрики -->
        <div class="grid" id="metrics"></div>
        
        <!-- Ресурсы с полосками -->
        <div class="section">
            <div class="section-title">💻 Ресурсы</div>
            <div id="resources"></div>
        </div>
        
        <!-- Службы -->
        <div class="section">
            <div class="section-title">🔧 Службы</div>
            <div id="services"></div>
        </div>
        
        <!-- Топ процессов -->
        <div class="section">
            <div class="section-title">⚡ Топ-5 процессов</div>
            <table>
                <thead><tr><th>PID</th><th>CPU</th><th>MEM</th><th>Процесс</th></tr></thead>
                <tbody id="processes"></tbody>
            </table>
        </div>
        
        <!-- Последние входы -->
        <div class="section">
            <div class="section-title">🔐 Последние входы SSH</div>
            <div id="sshLog" style="font-size:.85em;color:#888;"></div>
        </div>
        
        <div class="refresh">Обновлено: <span id="time"></span> • Автообновление каждые 10 сек</div>
    </div>
    
    <script>
        async function load() {
            try {
                const r = await fetch('/panel_data');
                const d = await r.json();
                
                // Метрики
                document.getElementById('metrics').innerHTML = `
                    <div class="card"><div class="card-value">${d.uptime}</div><div class="card-label">Аптайм</div></div>
                    <div class="card"><div class="card-value">${d.load}</div><div class="card-label">Нагрузка (1/5/15)</div></div>
                    <div class="card"><div class="card-value">${d.disk_percent}</div><div class="card-label">Диск занят</div></div>
                    <div class="card"><div class="card-value">${d.mem_percent}</div><div class="card-label">Память занята</div></div>
                `;
                
                // Ресурсы с полосками
                const cpuColor = d.cpu_percent > 80 ? 'fill-red' : d.cpu_percent > 50 ? 'fill-yellow' : 'fill-green';
                const memColor = d.mem_percent > 80 ? 'fill-red' : d.mem_percent > 50 ? 'fill-yellow' : 'fill-green';
                const diskColor = d.disk_percent > 80 ? 'fill-red' : d.disk_percent > 50 ? 'fill-yellow' : 'fill-green';
                
                document.getElementById('resources').innerHTML = `
                    <div style="margin-bottom:12px">
                        <div style="display:flex;justify-content:space-between"><span>CPU</span><span>${d.cpu_percent}%</span></div>
                        <div class="chart-bar"><div class="chart-fill ${cpuColor}" style="width:${d.cpu_percent}%"></div></div>
                    </div>
                    <div style="margin-bottom:12px">
                        <div style="display:flex;justify-content:space-between"><span>Память</span><span>${d.mem_used} / ${d.mem_total}</span></div>
                        <div class="chart-bar"><div class="chart-fill ${memColor}" style="width:${d.mem_percent}%"></div></div>
                    </div>
                    <div style="margin-bottom:12px">
                        <div style="display:flex;justify-content:space-between"><span>Диск</span><span>${d.disk_used} / ${d.disk_total}</span></div>
                        <div class="chart-bar"><div class="chart-fill ${diskColor}" style="width:${d.disk_percent}%"></div></div>
                    </div>
                `;
                
                // Службы
                document.getElementById('services').innerHTML = d.services.map(s => `
                    <div class="service-row">
                        <span class="service-name">${s.name}</span>
                        <span class="service-status ${s.active ? 'status-active' : 'status-inactive'}">${s.active ? '● Active' : '○ Inactive'}</span>
                    </div>
                `).join('');
                
                // Процессы
                document.getElementById('processes').innerHTML = d.processes.map(p => `
                    <tr><td>${p.pid}</td><td>${p.cpu}%</td><td>${p.mem}%</td><td style="word-break:break-all">${p.cmd}</td></tr>
                `).join('');
                
                // SSH
                document.getElementById('sshLog').textContent = d.ssh_logins || 'Нет данных';
                
                // Время
                document.getElementById('time').textContent = d.time;
            } catch(e) {
                console.error(e);
            }
        }
        
        load();
        setInterval(load, 10000);
    </script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

@app.route("/panel_data")
def panel_data():
    # Сбор всех данных
    uptime = run_bash("uptime -p | sed 's/up //'")
    load = run_bash("uptime | awk -F'load average:' '{print $2}' | xargs")
    
    cpu_percent = run_bash("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
    cpu_percent = cpu_percent.replace(",", ".") if cpu_percent else "0"
    
    mem_total = run_bash("free -h | grep Mem | awk '{print $2}'")
    mem_used = run_bash("free -h | grep Mem | awk '{print $3}'")
    mem_percent = run_bash("free | grep Mem | awk '{printf \"%.0f\", $3/$2*100}'")
    
    disk_total = run_bash("df -h / | tail -1 | awk '{print $2}'")
    disk_used = run_bash("df -h / | tail -1 | awk '{print $3}'")
    disk_percent = run_bash("df -h / | tail -1 | awk '{print $5}' | tr -d '%'")
    
    # Службы
    services_list = ["postgresql", "redis-server", "nginx", "ssh"]
    services = []
    for svc in services_list:
        active = run_bash(f"systemctl is-active {svc}") == "active"
        services.append({"name": svc, "active": active})
    
    # Процессы
    proc_raw = run_bash("ps aux --sort=-%cpu --no-headers | head -5 | awk '{print $2,$3,$4,$11}'")
    processes = []
    if proc_raw:
        for line in proc_raw.split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                processes.append({
                    "pid": parts[0],
                    "cpu": parts[1],
                    "mem": parts[2],
                    "cmd": " ".join(parts[3:])[:60]
                })
    
    # SSH-логины
    ssh_logins = run_bash("last -5 | awk '{print $1,$3,$4,$5,$6,$7}' | head -5")
    
    return jsonify({
        "time": datetime.now().strftime("%H:%M:%S"),
        "uptime": uptime,
        "load": load,
        "cpu_percent": float(cpu_percent) if cpu_percent else 0,
        "mem_total": mem_total,
        "mem_used": mem_used,
        "mem_percent": int(mem_percent) if mem_percent else 0,
        "disk_total": disk_total,
        "disk_used": disk_used,
        "disk_percent": int(disk_percent) if disk_percent else 0,
        "services": services,
        "processes": processes,
        "ssh_logins": ssh_logins,
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
