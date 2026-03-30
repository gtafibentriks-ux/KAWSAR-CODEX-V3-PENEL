import os
import sys
import subprocess
import threading
import time
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template_string, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_socketio import SocketIO

os.environ['PYTHONUNBUFFERED'] = '1'

# ── Logo base64 লোড ────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_logo_path = os.path.join(_here, "logo_b64.txt")
if os.path.exists(_logo_path):
    with open(_logo_path) as _f:
        LOGO_B64 = _f.read().strip()
else:
    # fallback: blank 1x1 transparent PNG
    LOGO_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# ── Flask + SocketIO ────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bot_secret_access_key_2026_99")
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    logger=False,
    engineio_logger=False
)

user_sessions = {}
ADMIN_CONFIG = "admin_config.txt"

# ══════════════════════════════════════════════════════════════════════════════
#  SPLASH PAGE HTML  (app.py এর নিজস্ব পেজ)
# ══════════════════════════════════════════════════════════════════════════════
SPLASH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>KAWSAR CODEX</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet"/>
<style>
  :root{--sky:#00d4ff;--sky2:#0099cc;--dark:#010d14;--glow:0 0 18px #00d4ff88,0 0 40px #00d4ff33;}
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Rajdhani',sans-serif;background:var(--dark);color:#e0f8ff;
    min-height:100vh;display:flex;flex-direction:column;align-items:center;overflow-x:hidden;position:relative;}

  /* bg */
  .bg{position:fixed;inset:0;z-index:0;
    background:radial-gradient(ellipse 80% 60% at 50% 0%,#002233 0%,#010d14 70%);}
  .bg::before{content:'';position:absolute;inset:0;
    background:repeating-linear-gradient(0deg,transparent,transparent 48px,rgba(0,212,255,.04) 49px),
               repeating-linear-gradient(90deg,transparent,transparent 48px,rgba(0,212,255,.04) 49px);
    animation:gridMove 8s linear infinite;}
  @keyframes gridMove{to{background-position:0 50px,50px 0;}}
  .particle{position:absolute;border-radius:50%;background:var(--sky);opacity:0;
    animation:float var(--dur,6s) var(--delay,0s) infinite ease-in-out;}
  @keyframes float{0%{transform:translateY(100vh) scale(0);opacity:0;}
    10%{opacity:.6;}80%{opacity:.3;}100%{transform:translateY(-10vh) scale(1.5);opacity:0;}}

  /* layout */
  .wrapper{position:relative;z-index:1;width:100%;max-width:500px;
    padding:30px 18px;display:flex;flex-direction:column;align-items:center;gap:22px;}

  /* logo */
  .logo-wrap{width:115px;height:115px;border-radius:50%;overflow:hidden;
    border:2.5px solid var(--sky);box-shadow:var(--glow);
    animation:pulse 3s ease-in-out infinite;}
  @keyframes pulse{0%,100%{box-shadow:var(--glow);}
    50%{box-shadow:0 0 30px #00d4ffbb,0 0 60px #00d4ff55;}}
  .logo-wrap img{width:100%;height:100%;object-fit:cover;display:block;}

  /* brand */
  .brand{font-family:'Orbitron',sans-serif;font-size:1.55rem;font-weight:900;
    letter-spacing:2px;text-align:center;
    background:linear-gradient(90deg,#fff 0%,var(--sky) 50%,#fff 100%);
    background-size:200%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
    animation:shine 3s linear infinite;}
  @keyframes shine{to{background-position:200%;}}

  /* music bar */
  .music-bar{width:100%;background:rgba(0,180,220,.07);
    border:1px solid rgba(0,180,220,.25);border-radius:14px;
    padding:11px 16px;display:flex;align-items:center;gap:12px;}
  .music-icon{font-size:1.3rem;animation:spin 3s linear infinite;}
  @keyframes spin{to{transform:rotate(360deg);}}
  .music-info{flex:1;}
  .music-title{font-size:.88rem;color:var(--sky);font-weight:600;}
  .music-sub{font-size:.73rem;color:#669aaa;margin-top:2px;}
  .music-waves{display:flex;gap:3px;align-items:flex-end;height:20px;}
  .wave{width:4px;border-radius:2px;background:var(--sky);
    animation:wave .8s ease-in-out infinite alternate;}
  .wave:nth-child(2){animation-delay:.15s;height:10px;}
  .wave:nth-child(3){animation-delay:.3s;height:18px;}
  .wave:nth-child(4){animation-delay:.45s;height:8px;}
  .wave:nth-child(5){animation-delay:.6s;height:14px;}
  @keyframes wave{from{transform:scaleY(.4);}to{transform:scaleY(1);}}
  .music-toggle{background:none;border:1.5px solid var(--sky);border-radius:50%;
    width:32px;height:32px;cursor:pointer;color:var(--sky);font-size:.95rem;
    display:flex;align-items:center;justify-content:center;transition:background .2s;}
  .music-toggle:hover{background:rgba(0,212,255,.15);}

  /* open btn */
  .open-btn{padding:12px 38px;border-radius:40px;
    background:linear-gradient(135deg,var(--sky2),var(--sky));
    border:none;cursor:pointer;
    font-family:'Orbitron',sans-serif;font-size:.92rem;font-weight:700;
    color:#001a26;letter-spacing:1.5px;box-shadow:0 4px 20px #00d4ff55;
    transition:transform .2s,box-shadow .2s;position:relative;overflow:hidden;}
  .open-btn::after{content:'';position:absolute;top:-50%;left:-60%;
    width:50%;height:200%;background:rgba(255,255,255,.25);transform:skewX(-20deg);
    animation:btnShine 2.5s ease infinite;}
  @keyframes btnShine{0%{left:-60%;}60%,100%{left:140%;}}
  .open-btn:hover{transform:scale(1.07);box-shadow:0 6px 30px #00d4ffaa;}

  /* about btn */
  .about-btn{background:none;border:1.5px solid rgba(0,180,220,.4);
    border-radius:12px;padding:9px 26px;color:#88ddee;
    font-family:'Rajdhani',sans-serif;font-size:.93rem;
    cursor:pointer;letter-spacing:1px;transition:border .2s,color .2s;}
  .about-btn:hover{border-color:var(--sky);color:var(--sky);}

  /* modal overlay */
  .modal-overlay{display:none;position:fixed;inset:0;z-index:100;
    background:rgba(0,10,20,.85);backdrop-filter:blur(6px);
    align-items:center;justify-content:center;}
  .modal-overlay.active{display:flex;}
  .modal{background:linear-gradient(135deg,#011824,#002233);
    border:1.5px solid var(--sky);border-radius:18px;
    padding:30px 26px;width:90%;max-width:370px;
    box-shadow:0 0 40px #00d4ff44;
    animation:modalIn .35s cubic-bezier(.34,1.56,.64,1);}
  @keyframes modalIn{from{transform:scale(.7);opacity:0;}to{transform:scale(1);opacity:1;}}
  .modal h2{font-family:'Orbitron',sans-serif;font-size:1rem;
    color:var(--sky);text-align:center;margin-bottom:20px;letter-spacing:1px;}

  /* steps */
  .steps{display:flex;flex-direction:column;gap:9px;}
  .step{display:flex;align-items:center;gap:11px;
    background:rgba(0,180,220,.07);border-radius:10px;
    padding:9px 13px;border:1px solid transparent;}
  .step-pct{font-family:'Orbitron',sans-serif;font-weight:900;font-size:1rem;
    color:var(--sky);min-width:44px;}
  .step-bar-wrap{flex:1;height:6px;background:#003344;border-radius:3px;overflow:hidden;}
  .step-bar{height:100%;width:0;background:linear-gradient(90deg,var(--sky2),var(--sky));
    border-radius:3px;transition:width 1.2s ease;}
  .step-label{font-size:.82rem;color:#88ddee;min-width:65px;text-align:right;}

  /* launch btn */
  .launch-btn{display:none;margin-top:18px;width:100%;padding:13px;
    border-radius:10px;background:linear-gradient(90deg,var(--sky2),var(--sky));
    border:none;cursor:pointer;font-family:'Orbitron',sans-serif;
    font-size:.92rem;font-weight:700;color:#001a26;letter-spacing:1px;
    box-shadow:0 4px 20px #00d4ff44;transition:transform .2s;}
  .launch-btn:hover{transform:scale(1.03);}

  /* about modal */
  .about-modal{display:none;position:fixed;inset:0;z-index:200;
    background:rgba(0,10,20,.9);backdrop-filter:blur(8px);
    align-items:center;justify-content:center;}
  .about-modal.active{display:flex;}
  .about-card{background:linear-gradient(135deg,#011824,#002233);
    border:1.5px solid var(--sky);border-radius:20px;
    padding:34px 30px;width:90%;max-width:340px;
    box-shadow:0 0 50px #00d4ff33;
    animation:modalIn .35s cubic-bezier(.34,1.56,.64,1);text-align:center;}
  .about-card h3{font-family:'Orbitron',sans-serif;color:var(--sky);
    font-size:.95rem;margin-bottom:22px;letter-spacing:2px;}
  .about-row{display:flex;justify-content:space-between;
    padding:9px 0;border-bottom:1px solid rgba(0,180,220,.15);font-size:.93rem;}
  .about-row:last-of-type{border-bottom:none;}
  .about-key{color:#669aaa;font-weight:600;}
  .about-val{color:#e0f8ff;font-weight:600;}
  .close-about{margin-top:20px;padding:9px 28px;border-radius:8px;
    background:linear-gradient(90deg,var(--sky2),var(--sky));
    border:none;cursor:pointer;font-family:'Orbitron',sans-serif;
    font-size:.83rem;font-weight:700;color:#001a26;}
</style>
</head>
<body>
<div class="bg" id="bgEl"></div>

<!-- auto music -->
<audio id="bgMusic" loop>
  <source src="/static/song.mp3" type="audio/mp4"/>
  <source src="/static/song.mp3" type="audio/mpeg"/>
</audio>

<div class="wrapper">
  <!-- logo -->
  <div class="logo-wrap">
    <img src="data:image/png;base64,{{ logo }}" alt="KAWSAR CODEX"/>
  </div>

  <!-- brand -->
  <div class="brand">KAWSAR CODEX</div>

  <!-- music bar -->
  <div class="music-bar">
    <span class="music-icon">🎵</span>
    <div class="music-info">
      <div class="music-title">Now Playing</div>
      <div class="music-sub">song.mp3 · KAWSAR CODEX</div>
    </div>
    <div class="music-waves" id="waves">
      <div class="wave" style="height:8px"></div>
      <div class="wave"></div><div class="wave"></div>
      <div class="wave"></div><div class="wave"></div>
    </div>
    <button class="music-toggle" id="muteBtn" title="Mute/Unmute">🔊</button>
  </div>

  <!-- open -->
  <button class="open-btn" onclick="openMenu()">⚡ OPEN</button>

  <!-- about -->
  <button class="about-btn" onclick="openAbout()">👨‍💻 About Developer</button>
</div>

<!-- loading modal -->
<div class="modal-overlay" id="menuModal">
  <div class="modal">
    <h2>⚡ KAWSAR CODEX PANEL</h2>
    <div class="steps" id="stepsWrap"></div>
    <button class="launch-btn" id="launchBtn" onclick="window.location.href='/panel/login'">
      🚀 LAUNCH PANEL
    </button>
  </div>
</div>

<!-- about modal -->
<div class="about-modal" id="aboutModal">
  <div class="about-card">
    <h3>👨‍💻 ABOUT DEVELOPER</h3>
    <div class="about-row"><span class="about-key">NAME</span><span class="about-val">KAWSAR AHMED</span></div>
    <div class="about-row"><span class="about-key">AGE</span><span class="about-val">15</span></div>
    <div class="about-row"><span class="about-key">CLASS</span><span class="about-val">9</span></div>
    <div class="about-row"><span class="about-key">RELIGION</span><span class="about-val">ISLAM</span></div>
    <div class="about-row"><span class="about-key">REGION</span><span class="about-val">BANGLADESH</span></div>
    <button class="close-about" onclick="closeAbout()">CLOSE</button>
  </div>
</div>

<script>
/* particles */
const bg=document.getElementById('bgEl');
for(let i=0;i<28;i++){
  const p=document.createElement('div');p.className='particle';
  const s=Math.random()*6+3;
  p.style.cssText=`width:${s}px;height:${s}px;left:${Math.random()*100}%;
    --dur:${Math.random()*8+5}s;--delay:${Math.random()*6}s;`;
  bg.appendChild(p);
}

/* music */
const audio=document.getElementById('bgMusic');
const muteBtn=document.getElementById('muteBtn');
const wavesEl=document.getElementById('waves');
let muted=false;
function tryPlay(){
  audio.volume=0.6;
  audio.play().catch(()=>document.addEventListener('click',()=>audio.play(),{once:true}));
}
tryPlay();
muteBtn.addEventListener('click',()=>{
  muted=!muted;audio.muted=muted;
  muteBtn.textContent=muted?'🔇':'🔊';
  wavesEl.style.opacity=muted?'0.3':'1';
});

/* loading steps */
const STEPS=[10,20,30,40,50,60,70,80,90,100];
let built=false;
function openMenu(){
  document.getElementById('menuModal').classList.add('active');
  if(built)return;built=true;
  const wrap=document.getElementById('stepsWrap');
  STEPS.forEach((pct,i)=>{
    const d=document.createElement('div');d.className='step';
    d.innerHTML=`<span class="step-pct">${pct}%</span>
      <div class="step-bar-wrap"><div class="step-bar" id="b${i}"></div></div>
      <span class="step-label" id="l${i}">Waiting...</span>`;
    wrap.appendChild(d);
    setTimeout(()=>{
      document.getElementById('b'+i).style.width='100%';
      const lbl=document.getElementById('l'+i);
      lbl.textContent='✓ Done';lbl.style.color='#00ffaa';
      if(i===STEPS.length-1)setTimeout(()=>document.getElementById('launchBtn').style.display='block',600);
    },500+i*380);
  });
}
document.getElementById('menuModal').addEventListener('click',function(e){
  if(e.target===this)this.classList.remove('active');
});

/* about */
function openAbout(){document.getElementById('aboutModal').classList.add('active');}
function closeAbout(){document.getElementById('aboutModal').classList.remove('active');}
document.getElementById('aboutModal').addEventListener('click',function(e){
  if(e.target===this)this.classList.remove('active');
});
</script>
</body>
</html>
"""

# ══════════════════════════════════════════════════════════════════════════════
#  penel.py এর সব HTML  (LOGIN PAGE)
# ══════════════════════════════════════════════════════════════════════════════
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
            --neon-sky: #00d4ff;
            --neon-cyan: #00eaff;
            --neon-purple: #a78bfa;
            --neon-green: #4ade80;
            --bg: #05050a;
            --card: rgba(10, 25, 35, 0.78);
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            background: var(--bg); color: #e8f5ff;
            font-family: 'Rajdhani', 'Orbitron', sans-serif;
            height: 100vh; display: flex; justify-content: center;
            align-items: center; overflow: hidden; position: relative;
        }
        #particles { position: fixed; inset: 0; pointer-events: none; z-index: -2; opacity: 0.25; }
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
        .scanline {
            position: fixed; inset: 0; pointer-events: none; z-index: -1; opacity: 0.07;
            background: repeating-linear-gradient(to bottom, transparent 0, transparent 2px, rgba(0,212,255,0.09) 2px, rgba(0,212,255,0.09) 4px);
            animation: scan 9s linear infinite;
        }
        @keyframes scan { 0% { transform: translateY(-100%); } 100% { transform: translateY(100%); } }
        .glitch { position: relative; display: inline-block; animation: glitch 3.5s infinite; }
        .glitch::before, .glitch::after {
            content: attr(data-text); position: absolute; top: 0; left: 0;
            opacity: 0.8; clip: rect(0, 9999px, 0, 0);
        }
        .glitch::before { left: 2px; text-shadow: -2px 0 var(--neon-purple); animation: glitch-shift 2.2s infinite; }
        .glitch::after  { left: -2px; text-shadow: 2px 0 var(--neon-sky); animation: glitch-shift 2.8s infinite; }
        @keyframes glitch { 0%,100% { transform: translate(0); } 2% { transform: translate(-2px,2px); } 4% { transform: translate(2px,-2px); } }
        @keyframes glitch-shift { 0%,100% { clip: rect(0,9999px,0,0); } 5% { clip: rect(10px,9999px,30px,0); } 15% { clip: rect(40px,9999px,60px,0); } }
        .login-card {
            background: var(--card); padding: 45px 35px; border-radius: 20px; width: 360px;
            border: 1px solid rgba(0,212,255,0.3);
            box-shadow: 0 15px 40px rgba(0,0,0,0.7), inset 0 0 15px rgba(0,212,255,0.08);
            backdrop-filter: blur(12px); position: relative; overflow: hidden;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .login-card:hover {
            transform: translateY(-10px) rotateX(4deg) rotateY(4deg);
            box-shadow: 0 25px 60px rgba(0,212,255,0.35), 0 0 80px rgba(0,234,255,0.25);
        }
        @keyframes rgb-pulse {
            0%,100% { border-color: var(--neon-sky); box-shadow: 0 0 20px var(--neon-sky); }
            40%     { border-color: var(--neon-cyan); box-shadow: 0 0 20px var(--neon-cyan); }
            70%     { border-color: var(--neon-green); box-shadow: 0 0 20px var(--neon-green); }
        }
        .login-card::after {
            content: ''; position: absolute; inset: -2px;
            border: 2px solid transparent; animation: rgb-pulse 7s infinite; pointer-events: none;
        }
        .logo-section { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 35px; }
        .logo-icon {
            background: linear-gradient(135deg, var(--neon-sky), #0099cc);
            padding: 8px 12px; border-radius: 10px; font-size: 22px; font-weight: bold;
            box-shadow: 0 0 15px rgba(0,212,255,0.6); animation: pulse 2.5s infinite;
        }
        @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }
        .logo-text {
            font-size: 28px; font-weight: 900; letter-spacing: 4px;
            background: linear-gradient(90deg, var(--neon-sky), var(--neon-cyan), #a78bfa);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .input-group { margin-bottom: 25px; position: relative; }
        .label { font-size: 11px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px; color: #a0d0ff; display: flex; align-items: center; gap: 6px; }
        input {
            width: 100%; padding: 15px; background: rgba(5, 20, 30, 0.8);
            border: 1px solid #224466; border-radius: 12px; color: white; transition: all 0.3s;
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
            box-shadow: 0 0 20px rgba(0,212,255,0.5); transition: all 0.3s;
        }
        .login-btn:hover { transform: translateY(-3px); box-shadow: 0 0 35px rgba(0,212,255,0.7); }
        .login-btn::before {
            content: ''; position: absolute; inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
            transform: translateX(-100%); transition: 0.6s;
        }
        .login-btn:hover::before { transform: translateX(100%); }
        #msg {
            color: #ff6b6b; font-size: 14px; text-align: center;
            margin-bottom: 18px; display: none; animation: glitch 1.2s infinite alternate;
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
                msg.textContent = "FIELDS REQUIRED!"; msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 3000); return;
            }
            try {
                const resp = await fetch('/panel/api/login_auth', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: u, password: p })
                });
                const data = await resp.json();
                if (data.status === 'success') {
                    window.location.href = '/panel/';
                } else {
                    msg.textContent = "INVALID CREDENTIALS!"; msg.style.display = 'block';
                    setTimeout(() => msg.style.display = 'none', 3200);
                }
            } catch (err) {
                msg.textContent = "CONNECTION ERROR!"; msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 3000);
            }
        }
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

# ══════════════════════════════════════════════════════════════════════════════
#  Helper functions (penel.py থেকে)
# ══════════════════════════════════════════════════════════════════════════════
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

def save_config(password, duration):
    with open(ADMIN_CONFIG, 'w') as f:
        f.write(f"admin_password={password}\nglobal_duration={duration}\n")

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        return redirect(url_for('panel_login'))
    return wrap

def self_ping():
    """Keep-alive: নিজেকে ping করে যাতে free hosting ঘুমিয়ে না পড়ে"""
    import time
    time.sleep(30)  # startup delay
    while True:
        try:
            port = int(os.environ.get("PORT", 32385))
            requests.get(f"http://localhost:{port}/health", timeout=10)
        except Exception:
            pass
        time.sleep(240)  # প্রতি 4 মিনিটে ping

threading.Thread(target=self_ping, daemon=True).start()

def bot_watchdog(name):
    """বট crash করলে auto-restart করে — 24/7 uptime নিশ্চিত করে"""
    while True:
        if name not in user_sessions or not user_sessions[name]['running']:
            break
        proc = user_sessions[name].get('proc')
        if proc and proc.poll() is not None:  # process মরে গেছে
            socketio.emit('new_log', {'data': '⚠️ Bot crashed! Auto-restarting in 5s...', 'user': name})
            time.sleep(5)
            if name in user_sessions and user_sessions[name]['running']:
                try:
                    creds_file = os.path.join(_here, "KAWSAR_CODEX.txt")
                    new_proc = subprocess.Popen(
                        [sys.executable, '-u', os.path.join(_here, 'main.py')],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1, universal_newlines=True,
                        cwd=_here
                    )
                    user_sessions[name]['proc'] = new_proc
                    threading.Thread(target=stream_logs, args=(new_proc, name), daemon=True).start()
                    socketio.emit('new_log', {'data': '✅ Bot restarted successfully!', 'user': name})
                except Exception as e:
                    socketio.emit('new_log', {'data': f'❌ Restart failed: {e}', 'user': name})
                    user_sessions[name]['running'] = False
                    break
        time.sleep(10)

def expiry_monitor():
    while True:
        now = datetime.now()
        for name, data in list(user_sessions.items()):
            if data['running'] and data['end_time'] != "unlimited":
                if now > data['end_time']:
                    if data['proc']: data['proc'].terminate()
                    user_sessions[name]['running'] = False
                    socketio.emit('status_update', {'running': False, 'user': name})
        time.sleep(2)

threading.Thread(target=expiry_monitor, daemon=True).start()

def stream_logs(proc, name):
    try:
        for line in iter(proc.stdout.readline, ''):
            if line:
                socketio.emit('new_log', {'data': line.strip(), 'user': name})
        proc.stdout.close()
    except Exception as e:
        print(f"Logging error for {name}: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

# ── Splash (app.py এর home) ──────────────────────────────────────────────────
@app.route('/')
def splash():
    return render_template_string(SPLASH_HTML, logo=LOGO_B64)

# ── Panel routes (/panel/...) ─────────────────────────────────────────────────
@app.route('/panel/login')
@app.route('/panel/login/')
def panel_login():
    if 'logged_in' in session:
        return redirect(url_for('panel_index'))
    return render_template_string(LOGIN_HTML)

@app.route('/panel/api/login_auth', methods=['POST'])
def panel_login_auth():
    data = request.json
    u = data.get('username')
    p = data.get('password')
    if u == "TCPV3" and p == "KAWSARCODEX":
        session['logged_in'] = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid credentials!"})

@app.route('/panel/')
@app.route('/panel')
@login_required
def panel_index():
    template_path = os.path.join(_here, 'templates', 'new.html')
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return render_template_string(html_content, logo=LOGO_B64)
    return "<h2 style='color:red;font-family:monospace;padding:40px'>❌ templates/new.html ফাইল পাওয়া যাচ্ছে না।<br>Please create: templates/new.html</h2>", 500

# ── Song route ───────────────────────────────────────────────────────────────
@app.route('/static/song.mp3')
def serve_song():
    song_path = os.path.join(_here, 'static')
    if os.path.exists(os.path.join(song_path, 'song.mp3')):
        return send_from_directory(song_path, 'song.mp3')
    # fallback: check root directory
    if os.path.exists(os.path.join(_here, 'song.mp3')):
        return send_from_directory(_here, 'song.mp3')
    return jsonify({"error": "song.mp3 not found"}), 404

@app.route('/panel/logout')
def panel_logout():
    session.clear()
    return redirect(url_for('panel_login'))

@app.route('/panel/api/check_status', methods=['POST'])
@login_required
def panel_check_status():
    data = request.json
    name = data.get('name')
    if name in user_sessions and user_sessions[name]['running']:
        info = user_sessions[name]
        rem_sec = -1 if info['end_time'] == "unlimited" else int((info['end_time'] - datetime.now()).total_seconds())
        return jsonify({"running": True, "rem_sec": max(0, rem_sec)})
    return jsonify({"running": False})

@app.route('/panel/api/control', methods=['POST'])
@login_required
def panel_bot_control():
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
            proc = subprocess.Popen(
                [sys.executable, '-u', 'main.py'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True
            )
            end_time = "unlimited" if conf['duration'] == -1 else datetime.now() + timedelta(minutes=conf['duration'])
            user_sessions[name] = {'proc': proc, 'end_time': end_time, 'running': True, 'uid': uid, 'pw': pw}
            threading.Thread(target=stream_logs, args=(proc, name), daemon=True).start()
            threading.Thread(target=bot_watchdog, args=(name,), daemon=True).start()
            rem_sec = (conf['duration'] * 60 if conf['duration'] != -1 else -1)
            return jsonify({"status": "success", "running": True, "rem_sec": rem_sec})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    elif action == 'stop':
        if name in user_sessions and user_sessions[name]['running']:
            if user_sessions[name]['proc']: user_sessions[name]['proc'].terminate()
            user_sessions[name]['running'] = False
            return jsonify({"status": "success", "running": False})
    return jsonify({"status": "error", "message": "FAILED"})

@app.route('/panel/api/admin', methods=['POST'])
@login_required
def panel_admin_api():
    data = request.json
    conf = get_config()
    if data.get('password') != conf['pass']:
        return jsonify({"status": "error", "message": "Wrong Passkey!"})
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

@app.route('/panel/api/proxy_guild')
@login_required
def panel_proxy_guild():
    t   = request.args.get('type')
    gid = request.args.get('guild_id')
    reg = request.args.get('region')
    uid = request.args.get('uid')
    pw  = request.args.get('password')
    base_url = "https://guild-info-danger.vercel.app"
    urls = {
        'info':    f"{base_url}/guild?guild_id={gid}&region={reg}",
        'join':    f"{base_url}/join?guild_id={gid}&uid={uid}&password={pw}",
        'members': f"{base_url}/members?guild_id={gid}&uid={uid}&password={pw}",
        'leave':   f"{base_url}/leave?guild_id={gid}&uid={uid}&password={pw}"
    }
    try:
        resp = requests.get(urls.get(t), timeout=15)
        return jsonify(resp.json())
    except:
        return jsonify({"error": "API Error"})

# ══════════════════════════════════════════════════════════════════════════════
#  ALIAS ROUTES — new.html এ /api/... call আসে, তাই /panel/api/... এর সাথে
#  মিল রাখতে এই duplicate route গুলো দরকার
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/check_status', methods=['POST'])
@login_required
def api_check_status_alias():
    return panel_check_status()

@app.route('/api/control', methods=['POST'])
@login_required
def api_bot_control_alias():
    return panel_bot_control()

@app.route('/api/admin', methods=['POST'])
@login_required
def api_admin_alias():
    return panel_admin_api()

@app.route('/api/proxy_guild')
@login_required
def api_proxy_guild_alias():
    return panel_proxy_guild()

@app.route('/api/login_auth', methods=['POST'])
def api_login_auth_alias():
    return panel_login_auth()

# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/health')
def health():
    alive = sum(1 for s in user_sessions.values() if s.get('running'))
    return jsonify({"status": "ok", "active_bots": alive}), 200

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 32382))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
