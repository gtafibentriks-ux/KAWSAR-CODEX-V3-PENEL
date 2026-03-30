import os
import sys
import subprocess
import threading
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template_string
from flask_socketio import SocketIO

# রেন্ডার বা ক্লাউড হোস্টিংয়ের জন্য বাফারিং বন্ধ করা
os.environ['PYTHONUNBUFFERED'] = '1'

app = Flask(__name__)
# সেশন সিকিউরিটির জন্য সিক্রেট কি
app.secret_key = "bot_secret_access_key_2026_99" 
# রেন্ডারে রিয়েল-টাইম লগের জন্য async_mode threading বা eventlet ব্যবহার করা হয়
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ইউজার সেশন ডাটা স্টোর করার জন্য ডিকশনারি
user_sessions = {} 
ADMIN_CONFIG = "admin_config.txt"

# --- লগইন পেইজের ডিজাইন ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KAWSAR_CODEX • ACCESS TERMINAL</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --neon-sky: #00d4ff;       /* main sky-blue / neon cyan */
            --neon-cyan: #00eaff;
            --neon-purple: #a78bfa;     /* হালকা purple accent */
            --neon-green: #4ade80;
            --bg: #05050a;
            --card: rgba(10, 25, 35, 0.78);   /* sky-blue টোনের সাথে মিলিয়ে */
        }

        * { margin:0; padding:0; box-sizing:border-box; }

        body {
            background: var(--bg);
            color: #e8f5ff;
            font-family: 'Rajdhani', 'Orbitron', sans-serif;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            position: relative;
            cursor: none;
        }

        /* Custom Neon Cursor */
        body::before {
            content: '';
            position: fixed;
            width: 12px; height: 12px;
            background: var(--neon-sky);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 18px var(--neon-sky), 0 0 35px var(--neon-sky);
            transition: transform 0.1s ease-out;
            mix-blend-mode: difference;
            opacity: 0.9;
        }
        body:hover::before { transform: translate(-50%, -50%) scale(2); }

        /* Particles Background */
        #particles {
            position: fixed; inset: 0; pointer-events: none; z-index: -2; opacity: 0.25;
        }
        .particle {
            position: absolute; background: var(--neon-sky); border-radius: 50%;
            box-shadow: 0 0 8px var(--neon-sky);
            animation: floatParticle 22s infinite linear;
        }
        @keyframes floatParticle {
            0%   { transform: translateY(120vh) scale(0.2); opacity: 0; }
            15%  { opacity: 0.7; }
            85%  { opacity: 0.7; }
            100% { transform: translateY(-50vh) scale(0.5); opacity: 0; }
        }

        /* Scanline Overlay */
        .scanline {
            position: fixed; inset: 0; pointer-events: none; z-index: -1; opacity: 0.07;
            background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(0,212,255,0.09) 2px, rgba(0,212,255,0.09) 4px);
            animation: scan 9s linear infinite;
        }
        @keyframes scan { 0% { transform: translateY(-100%); } 100% { transform: translateY(100%); } }

        /* Glitch Animation */
        .glitch {
            position: relative; display: inline-block;
            animation: glitch 3.5s infinite;
        }
        .glitch::before, .glitch::after {
            content: attr(data-text);
            position: absolute; top: 0; left: 0;
            opacity: 0.8; clip: rect(0, 9999px, 0, 0);
        }
        .glitch::before { left: 2px; text-shadow: -2px 0 var(--neon-purple); animation: glitch-shift 2.2s infinite; }
        .glitch::after  { left: -2px; text-shadow: 2px 0 var(--neon-sky); animation: glitch-shift 2.8s infinite; }

        @keyframes glitch { 0%,100% { transform: translate(0); } 2% { transform: translate(-2px,2px); } 4% { transform: translate(2px,-2px); } }
        @keyframes glitch-shift { 0%,100% { clip: rect(0,9999px,0,0); } 5% { clip: rect(10px,9999px,30px,0); } 15% { clip: rect(40px,9999px,60px,0); } }

        .login-card {
            background: var(--card);
            padding: 45px 35px;
            border-radius: 20px;
            width: 360px;
            border: 1px solid rgba(0,212,255,0.3);
            box-shadow: 0 15px 40px rgba(0,0,0,0.7), inset 0 0 15px rgba(0,212,255,0.08);
            backdrop-filter: blur(12px);
            position: relative;
            overflow: hidden;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .login-card:hover {
            transform: translateY(-10px) rotateX(4deg) rotateY(4deg);
            box-shadow: 0 25px 60px rgba(0,212,255,0.35), 0 0 80px rgba(0,234,255,0.25);
        }

        /* RGB Pulse Border (sky-blue dominant) */
        @keyframes rgb-pulse {
            0%,100% { border-color: var(--neon-sky); box-shadow: 0 0 20px var(--neon-sky); }
            40%     { border-color: var(--neon-cyan); box-shadow: 0 0 20px var(--neon-cyan); }
            70%     { border-color: var(--neon-green); box-shadow: 0 0 20px var(--neon-green); }
        }
        .login-card::after {
            content: '';
            position: absolute; inset: -2px;
            border: 2px solid transparent;
            animation: rgb-pulse 7s infinite;
            pointer-events: none;
        }

        .logo-section {
            display: flex; align-items: center; justify-content: center; gap: 12px;
            margin-bottom: 35px;
        }
        .logo-icon {
            background: linear-gradient(135deg, var(--neon-sky), #0099cc);
            padding: 8px 12px; border-radius: 10px;
            font-size: 22px; font-weight: bold;
            box-shadow: 0 0 15px rgba(0,212,255,0.6);
            animation: pulse 2.5s infinite;
        }
        @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }

        .logo-text { 
            font-size: 28px; font-weight: 900; letter-spacing: 4px;
            background: linear-gradient(90deg, var(--neon-sky), var(--neon-cyan), #a78bfa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        .input-group { margin-bottom: 25px; position: relative; }
        .label {
            font-size: 11px; font-weight: bold; text-transform: uppercase;
            margin-bottom: 8px; color: #a0d0ff; display: flex; align-items: center; gap: 6px;
        }
        input {
            width: 100%; padding: 15px; background: rgba(5, 20, 30, 0.8);
            border: 1px solid #224466; border-radius: 12px; color: white;
            transition: all 0.3s;
        }
        input:focus {
            border-color: var(--neon-sky);
            box-shadow: 0 0 15px rgba(0,212,255,0.5), inset 0 0 8px rgba(0,212,255,0.2);
            transform: scale(1.02);
        }

        .login-btn {
            background: linear-gradient(90deg, var(--neon-sky), #00aaff);
            color: white; border: none; width: 100%; padding: 15px;
            border-radius: 12px; font-weight: bold; cursor: pointer;
            display: flex; align-items: center; justify-content: center; gap: 10px;
            text-transform: uppercase; font-size: 15px; margin-top: 15px;
            position: relative; overflow: hidden;
            box-shadow: 0 0 20px rgba(0,212,255,0.5);
            transition: all 0.3s;
        }
        .login-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 0 35px rgba(0,212,255,0.7);
        }
        .login-btn::before {
            content: ''; position: absolute; inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
            transform: translateX(-100%); transition: 0.6s;
        }
        .login-btn:hover::before { transform: translateX(100%); }

        #msg {
            color: #ff6b6b; font-size: 14px; text-align: center;
            margin-bottom: 18px; display: none;
            animation: glitch 1.2s infinite alternate;
        }

        .info-footer {
            margin-top: 35px; background: rgba(5, 20, 30, 0.6);
            padding: 15px; border-radius: 12px; font-size: 11px;
            text-align: center; color: #88aaff; border: 1px solid #224466;
        }
        .info-footer span { color: var(--neon-sky); font-weight: bold; display: block; margin-bottom: 6px; }
    </style>
</head>
<body>

    <div id="particles"></div>
    <div class="scanline"></div>

    <div class="login-card">
        <div class="logo-section">
            <div class="logo-icon glitch" data-text="🎮">🎮</div>
            <div class="logo-text glitch" data-text="KAWSAR_CODEX">KAWSAR_CODEX</div>
        </div>

        <div id="msg" class="glitch" data-text="ACCESS DENIED!">ACCESS DENIED!</div>

        <div class="input-group">
            <div class="label">👤 USERNAME</div>
            <input type="text" id="u" placeholder="Enter username" autocomplete="off">
        </div>

        <div class="input-group">
            <div class="label">🔒 PASSWORD</div>
            <input type="password" id="p" placeholder="Enter password">
        </div>

        <button class="login-btn" onclick="doLogin()">➜ AUTHENTICATE</button>

        <div class="info-footer">
            <span>DEFAULT CREDENTIALS</span>
            TCPV3 / KAWSARCODEX<br>
            Developer @KAWSAR_CODEX
        </div>
    </div>

    <script>
        async function doLogin() {
            const u = document.getElementById('u').value.trim();
            const p = document.getElementById('p').value;
            const msg = document.getElementById('msg');

            if (!u || !p) {
                msg.textContent = "FIELDS REQUIRED!";
                msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 3000);
                return;
            }

            try {
                const resp = await fetch('/api/login_auth', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: u, password: p })
                });
                const data = await resp.json();

                if (data.status === 'success') {
                    window.location.href = '/';
                } else {
                    msg.textContent = "INVALID CREDENTIALS!";
                    msg.style.display = 'block';
                    setTimeout(() => msg.style.display = 'none', 3200);
                }
            } catch (err) {
                msg.textContent = "CONNECTION ERROR!";
                msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 3000);
            }
        }

        // Particles
        function createParticles() {
            const cont = document.getElementById('particles');
            for (let i = 0; i < 30; i++) {
                const p = document.createElement('div');
                p.className = 'particle';
                p.style.width = p.style.height = (Math.random() * 4 + 1.5) + 'px';
                p.style.left = Math.random() * 100 + 'vw';
                p.style.animationDelay = Math.random() * 18 + 's';
                p.style.animationDuration = (Math.random() * 15 + 15) + 's';
                cont.appendChild(p);
            }
        }
        createParticles();
    </script>
</body>
</html>
"""

# অ্যাডমিন কনফিগারেশন লোড করা
def get_config():
    conf = {"pass": "admin123", "duration": 120}
    if os.path.exists(ADMIN_CONFIG):
        with open(ADMIN_CONFIG, 'r') as f:
            for line in f:
                if '=' in line:
                    parts = line.strip().split('=')
                    if len(parts) == 2:
                        key, val = parts
                        if key == 'admin_password': conf['pass'] = val
                        if key == 'global_duration': conf['duration'] = int(val)
    return conf

# অ্যাডমিন কনফিগারেশন সেভ করা
def save_config(password, duration):
    with open(ADMIN_CONFIG, 'w') as f:
        f.write(f"admin_password={password}\nglobal_duration={duration}\n")

# লগইন চেক করার ডেকোরেটর
def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        return redirect(url_for('login'))
    wrap.__name__ = f.__name__
    return wrap

# বটের এক্সপায়ারি চেক করার মনিটর
def expiry_monitor():
    while True:
        now = datetime.now()
        for name, data in list(user_sessions.items()):
            if data['running'] and data['end_time'] != "unlimited":
                if now > data['end_time']:
                    if data['proc']:
                        data['proc'].terminate()
                    user_sessions[name]['running'] = False
                    socketio.emit('status_update', {'running': False, 'user': name})
        time.sleep(2)

threading.Thread(target=expiry_monitor, daemon=True).start()

def stream_logs(proc, name):
    try:
        # রিয়েল-টাইম লগের জন্য iter এবং readline ব্যবহার
        for line in iter(proc.stdout.readline, ''):
            if line:
                socketio.emit('new_log', {'data': line.strip(), 'user': name})
        proc.stdout.close()
    except Exception as e:
        print(f"Logging error for {name}: {e}")

# --- রুটস (Routes) ---

@app.route('/login')
def login():
    if 'logged_in' in session:
        return redirect(url_for('index'))
    return render_template_string(LOGIN_HTML)

@app.route('/api/login_auth', methods=['POST'])
def login_auth():
    data = request.json
    u = data.get('username')
    p = data.get('password')
    if u == "TCPV3" and p == "KAWSARCODEX":
        session['logged_in'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid credentials!"})

@app.route('/')
@login_required
def index():
    return render_template('new.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/check_status', methods=['POST'])
@login_required
def check_status():
    data = request.json
    name = data.get('name')
    if name in user_sessions and user_sessions[name]['running']:
        info = user_sessions[name]
        rem_sec = -1 if info['end_time'] == "unlimited" else int((info['end_time'] - datetime.now()).total_seconds())
        return jsonify({"running": True, "rem_sec": max(0, rem_sec)})
    return jsonify({"running": False})

@app.route('/api/control', methods=['POST'])
@login_required
def bot_control():
    data = request.json
    action, name, uid, pw = data.get('action'), data.get('name'), data.get('uid'), data.get('password')
    conf = get_config()

    if action == 'start':
        if not uid or not pw:
            return jsonify({"status": "error", "message": "UID/PW required!"})
        if name in user_sessions and user_sessions[name]['running']:
            return jsonify({"status": "error", "message": "ALREADY RUNNING!"})
        try:
            with open("KAWSAR_CODEX.txt", "w") as f: f.write(f"uid={uid}\npassword={pw}")
            
            # সংশোধনী: sys.executable এর সাথে '-u' ফ্লাগ যুক্ত করা হয়েছে যেন লগ সাথে সাথে আসে
            proc = subprocess.Popen(
                [sys.executable, '-u', 'main.py'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                bufsize=1, 
                universal_newlines=True
            )
            
            end_time = "unlimited" if conf['duration'] == -1 else datetime.now() + timedelta(minutes=conf['duration'])
            user_sessions[name] = {'proc': proc, 'end_time': end_time, 'running': True}
            
            threading.Thread(target=stream_logs, args=(proc, name), daemon=True).start()
            
            rem_sec = (conf['duration'] * 60 if conf['duration'] != -1 else -1)
            return jsonify({"status": "success", "running": True, "rem_sec": rem_sec})
        except Exception as e: 
            return jsonify({"status": "error", "message": str(e)})

    elif action == 'stop':
        if name in user_sessions and user_sessions[name]['running']:
            if user_sessions[name]['proc']: 
                user_sessions[name]['proc'].terminate()
            user_sessions[name]['running'] = False
            return jsonify({"status": "success", "running": False})
    return jsonify({"status": "error", "message": "FAILED"})

@app.route('/api/admin', methods=['POST'])
@login_required
def admin_api():
    data = request.json
    conf = get_config()
    if data.get('password') != conf['pass']: return jsonify({"status": "error", "message": "Wrong Passkey!"})
    action = data.get('action')
    if action == 'login':
        active_users = []
        for n, i in user_sessions.items():
            if i['running']:
                rem_m = -1 if i['end_time'] == "unlimited" else max(0, int((i['end_time'] - datetime.now()).total_seconds() / 60))
                active_users.append({"name": n, "rem_min": rem_m})
        return jsonify({"status": "success", "duration": conf['duration'], "users": active_users})
    elif action == 'save_global':
        save_config(conf['pass'], int(data.get('duration', 120)))
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/api/proxy_guild')
@login_required
def proxy_guild():
    t, gid, reg, uid, pw = request.args.get('type'), request.args.get('guild_id'), request.args.get('region'), request.args.get('uid'), request.args.get('password')
    base_url = "https://guild-info-danger.vercel.app"
    urls = {
        'info': f"{base_url}/guild?guild_id={gid}&region={reg}",
        'join': f"{base_url}/join?guild_id={gid}&uid={uid}&password={pw}",
        'members': f"{base_url}/members?guild_id={gid}&uid={uid}&password={pw}",
        'leave': f"{base_url}/leave?guild_id={gid}&uid={uid}&password={pw}"
    }
    try:
        resp = requests.get(urls.get(t), timeout=15)
        return jsonify(resp.json())
    except: return jsonify({"error": "API Error"})

if __name__ == '__main__':
    # Render-এ পোর্ট এনভায়রনমেন্ট ভেরিয়েবল থেকে নিতে হয়
    port = int(os.environ.get("PORT", 3146))
    # Render-এ রিয়েল-টাইম লগের জন্য host '0.0.0.0' হওয়া বাধ্যতামূলক
    socketio.run(app, host='0.0.0.0', port=port)
