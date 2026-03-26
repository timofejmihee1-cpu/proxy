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

# --- [ ЛОГИКА ПРОКСИ ] ---
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

def get_fresh_proxies(limit=8):
    sources = ["https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"]
    try:
        r = requests.get(sources[0], timeout=5)
        raw_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text)
        unique = list(set(raw_list))
        random.shuffle(unique)
        with ThreadPoolExecutor(max_workers=30) as executor:
            results = list(executor.map(check_proxy, unique[:60]))
        return sorted([r for r in results if r], key=lambda x: x['ms'])[:limit]
    except: return []

# --- [ ВЕБ-САЙТ ] ---
app = Flask('')
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Proxy Hunter Web + Casino</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 20px; border: 1px solid #334155; }
        .proxy-card { background: #334155; margin: 10px 0; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
        .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 15px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .casino-box { margin-top: 30px; padding: 20px; border: 2px dashed #f59e0b; border-radius: 15px; }
        #wheel { width: 80px; height: 80px; border: 4px solid #f59e0b; border-radius: 50%; margin: 15px auto; display: flex; align-items: center; justify-content: center; font-size: 40px; }
        .spinning { animation: spin 0.3s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        #res-link { display: none; margin-top: 15px; padding: 12px; background: #22c55e; border-radius: 8px; color: white; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰 PROXY HUNTER</h1>
        {% for p in proxies %}
        <div class="proxy-card">
            <div style="text-align:left"><b>{{ p.icon }} {{ p.ms }}ms</b><br><small style="color:#94a3b8">{{ p.server[:20] }}</small></div>
            <a href="{{ p.url }}" class="btn">ВКЛЮЧИТЬ</a>
        </div>
        {% endfor %}
        <div class="casino-box">
            <h3>🎰 ПРОКСИ-КАЗИНО</h3>
            <div id="wheel">🎲</div>
            <button onclick="spin()" id="spin-btn" class="btn" style="background:#f59e0b;">КРУТИТЬ</button>
            <a href="#" id="res-link"></a>
        </div>
    </div>
    <script>
        const px = {{ px_json | safe }};
        function spin() {
            const w = document.getElementById('wheel');
            const b = document.getElementById('spin-btn');
            const r = document.getElementById('res-link');
            b.disabled = true; r.style.display = 'none'; w.classList.add('spinning');
            setTimeout(() => {
                w.classList.remove('spinning');
                const p = px[Math.floor(Math.random()*px.length)];
                w.innerHTML = p.icon; r.href = p.url; r.style.display = 'block';
                r.innerHTML = "✅ ВЫПАЛ " + p.ms + "ms - ЖМИ!"; b.disabled = false;
            }, 2000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
    return render_template_string(HTML_TEMPLATE, proxies=proxies, px_json=json.dumps(proxies), support=SUPPORT_LINK)

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    text = (
        "🦾 **PROXY HUNTER v14.3**\n\n"
        "🛰 /get — Поиск быстрых прокси\n"
        "❓ /help — Помощь и поддержка"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "🛰 **Ищу лучшие варианты...**")
    valid = get_fresh_proxies(6)
    if valid:
        res = "📡 **АКТУАЛЬНЫЕ MTPROTO:**\n\n"
        for p in valid: res += f"{p['icon']} **{p['ms']}ms** — {p['url']}\n\n"
        res += "⚠️ **ВНИМАНИЕ:**\nНекоторые прокси могут не работать из-за ограничений твоего **оператора** или **Wi-Fi**. Если не грузит — попробуй следующий."
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = (
        "❓ **ИНФОРМАЦИЯ**\n\n"
        "🟢 — Быстро | 🟡 — Средне | 🔴 — Медленно\n\n"
        "🛑 **ПРОБЛЕМЫ?**\n"
        "Если прокси не подключается, попробуйте сменить тип интернета (Wi-Fi/4G) или выбрать другой вариант в списке.\n\n"
        "💡 **ЕСТЬ ИДЕЯ?**\n"
        "Мы всегда рады вашим предложениям! Пишите в нашу поддержку: [КЛИК СЮДА](" + SUPPORT_LINK + ")"
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

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
