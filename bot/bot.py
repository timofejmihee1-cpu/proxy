import telebot
import requests
import re
import time
import random
import socket
import json
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template_string
from threading import Thread

# --- [ КОНФИГ ] ---
TOKEN = '8764406808:AAEwgPjf4K4CxJ8ZUfDy8G2XOCYCoP2a1HM'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa"
WEB_URL = "https://proxy-rhe6.onrender.com"

bot = telebot.TeleBot(TOKEN)
users = set()

# --- [ ЛОГИКА ПРОВЕРКИ ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
        sock = socket.create_connection((srv, int(prt)), timeout=0.8)
        sock.close()
        ms = int((time.time() - start) * 1000)
        icon = "🟢" if ms < 150 else "🟡" if ms < 300 else "🔴"
        return {'ms': ms, 'icon': icon, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}", 'server': srv}
    except: return None

def get_fresh_proxies(limit=10):
    sources = ["https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"]
    try:
        r = requests.get(sources[0], timeout=5)
        raw_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text)
        unique = list(set(raw_list))
        random.shuffle(unique)
        with ThreadPoolExecutor(max_workers=25) as executor:
            results = list(executor.map(check_proxy, unique[:50]))
        return sorted([r for r in results if r], key=lambda x: x['ms'])[:limit]
    except: return []

# --- [ ВЕБ-САЙТ С КАЗИНО ] ---
app = Flask('')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Proxy Hunter Casino</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 20px; box-shadow: 0 15px 30px rgba(0,0,0,0.4); }
        h1 { color: #38bdf8; }
        .proxy-card { background: #334155; margin: 10px 0; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
        .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 15px; border-radius: 8px; font-weight: bold; cursor: pointer; border: none; }
        
        /* Стили Казино */
        .casino-box { margin-top: 30px; padding: 20px; border: 2px dashed #38bdf8; border-radius: 15px; background: #1e293b; }
        #wheel { width: 100px; height: 100px; border: 5px solid #38bdf8; border-radius: 50%; margin: 15px auto; transition: transform 3s cubic-bezier(0.1, 0.7, 1.0, 0.1); display: flex; align-items: center; justify-content: center; font-size: 30px; }
        .spinning { animation: spin 0.5s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        #result-link { display: none; margin-top: 15px; padding: 10px; background: #22c55e; border-radius: 8px; color: white; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰 PROXY HUNTER</h1>
        <div id="proxy-list">
            {% for p in proxies %}
            <div class="proxy-card">
                <div style="text-align:left"><b>{{ p.icon }} {{ p.ms }}ms</b><br><small style="color:#94a3b8">{{ p.server[:20] }}</small></div>
                <a href="{{ p.url }}" class="btn">ВКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
        </div>

        <div class="casino-box">
            <h3>🎰 ПРОКСИ-КАЗИНО</h3>
            <p style="font-size: 12px; color: #94a3b8;">Не хочешь выбирать? Пусть решит удача!</p>
            <div id="wheel">🎲</div>
            <button onclick="spinWheel()" id="spin-button" class="btn" style="background: #f59e0b;">КРУТИТЬ КОЛЕСО</button>
            <a href="#" id="result-link">ПОДКЛЮЧИТЬ ВЫПАВШИЙ</a>
        </div>

        <p style="font-size:12px; color:#64748b; margin-top:20px;">Создано Тимофеем | <a href="{{ support }}" style="color:#38bdf8">Поддержка</a></p>
    </div>

    <script>
        const proxies = {{ proxies_json | safe }};
        function spinWheel() {
            if (proxies.length === 0) return alert("Сначала обнови страницу!");
            const wheel = document.getElementById('wheel');
            const btn = document.getElementById('spin-button');
            const resLink = document.getElementById('result-link');
            
            btn.disabled = True;
            resLink.style.display = 'none';
            wheel.classList.add('spinning');
            
            setTimeout(() => {
                wheel.classList.remove('spinning');
                const randomProxy = proxies[Math.floor(Math.random() * proxies.length)];
                wheel.innerHTML = randomProxy.icon;
                resLink.href = randomProxy.url;
                resLink.style.display = 'block';
                resLink.innerHTML = "ВЫПАЛ " + randomProxy.ms + "ms - ПОДКЛЮЧИТЬ";
                btn.disabled = false;
            }, 3000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
    return render_template_string(HTML_TEMPLATE, 
                               proxies=proxies, 
                               proxies_json=json.dumps(proxies), 
                               support=SUPPORT_LINK)

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    bot.send_message(m.chat.id, "🦾 **PROXY HUNTER v14.0**\n\nТеперь с Казино на сайте! Крути и выбирай лучший прокси.")

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "🛰 **Ищу лучшие варианты...**")
    valid = get_fresh_proxies(6)
    if valid:
        res = "📡 **АКТУАЛЬНЫЕ MTPROTO:**\n\n"
        for p in valid: res += f"{p['icon']} **{p['ms']}ms** — {p['url']}\n\n"
        res += "⚠️ Не грузит? Пробуй другой или крути колесо на сайте: " + WEB_URL
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = (
        "❓ **ИНФОРМАЦИЯ**\n\n"
        "🟢 — Пинг отличный | 🟡 — Средний | 🔴 — Медленно\n\n"
        "💡 **ЕСТЬ ИДЕЯ?**\n"
        "Пишите в нашу поддержку: [КЛИК СЮДА](" + SUPPORT_LINK + ")"
    )
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        valid = get_fresh_proxies(5)
        if valid:
            post_text = "🛰 **СВЕЖИЕ ПРОКСИ + КАЗИНО**\n\n"
            for p in valid: post_text += f"{p['icon']} Пинг: **{p['ms']}ms**\n{p['url']}\n\n"
            post_text += f"🌐 Наш сайт: {WEB_URL}\n📢 Подпишись на {CHANNEL_ID}"
            bot.send_message(CHANNEL_ID, post_text, disable_web_page_preview=True)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **ADMIN**\nЮзеров: {len(users)}\n/post — Пост в канал")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
