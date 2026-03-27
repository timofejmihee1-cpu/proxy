import telebot
import requests
import re
import time
import random
import socket
import json
import os
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template_string
from threading import Thread

# --- [ КОНФИГ ] ---
# Брат, теперь токен в безопасности в настройках Render
TOKEN = os.getenv("BOT_TOKEN") 

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
        # Таймаут 0.8 как в оригинальной 14.3
        sock = socket.create_connection((srv, int(prt)), timeout=0.8)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        if ms < 150: icon = "🟢"
        elif ms < 300: icon = "🟡"
        else: icon = "🔴"
            
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

# ТОТ САМЫЙ ПИНГ, КОТОРЫЙ ТЫ ПРОСИЛ
@app.route('/ping')
def ping():
    return "OK", 200

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
    # Твой полный HTML со всеми строчками и оформлением
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Proxy Hunter Web + Casino</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: #0f172a; color: #f8fafc; font-family: -apple-system, sans-serif; text-align: center; padding: 20px; margin: 0; }
            .container { max-width: 500px; margin: 20px auto; background: #1e293b; padding: 25px; border-radius: 20px; box-shadow: 0 15px 30px rgba(0,0,0,0.4); border: 1px solid #334155; }
            h1 { color: #38bdf8; font-size: 28px; }
            .proxy-card { background: #334155; margin-bottom: 12px; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
            .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; border: none; }
            .casino-box { margin-top: 30px; padding: 20px; border: 2px dashed #f59e0b; border-radius: 15px; background: #1e293b; }
            #wheel { width: 80px; height: 80px; border: 4px solid #f59e0b; border-radius: 50%; margin: 15px auto; display: flex; align-items: center; justify-content: center; font-size: 40px; transition: transform 0.5s; }
            .spinning { animation: spin 0.3s linear infinite; }
            @keyframes spin { 100% { transform: rotate(360deg); } }
            #result-link { display: none; margin-top: 15px; padding: 12px; background: #22c55e; border-radius: 8px; color: white; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛰 PROXY HUNTER</h1>
            {% for p in proxies %}
            <div class="proxy-card">
                <div style="text-align:left"><b>{{ p.icon }} {{ p.ms }}ms</b><br><small>{{ p.server[:20] }}</small></div>
                <a href="{{ p.url }}" class="btn">ВКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
            <div class="casino-box">
                <h3 style="color:#f59e0b;">🎰 ПРОКСИ-КАЗИНО</h3>
                <div id="wheel">🎲</div>
                <button onclick="spin()" id="spin-btn" class="btn" style="background:#f59e0b;">КРУТИТЬ</button>
                <a href="#" id="result-link"></a>
            </div>
        </div>
        <script>
            const px = {{ px_json | safe }};
            function spin() {
                const w = document.getElementById('wheel');
                const b = document.getElementById('spin-btn');
                const r = document.getElementById('result-link');
                b.disabled = true; r.style.display = 'none'; w.classList.add('spinning');
                setTimeout(() => {
                    w.classList.remove('spinning');
                    const p = px[Math.floor(Math.random()*px.length)];
                    w.innerHTML = p.icon; r.href = p.url; r.style.display = 'block';
                    r.innerHTML = "✅ ВЫПАЛ " + p.ms + "ms"; b.disabled = false;
                }, 2000);
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(HTML_TEMPLATE, proxies=proxies, px_json=json.dumps(proxies))

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    bot.send_message(m.chat.id, "🦾 PROXY HUNTER v14.3\n\n/get — Прокси\n/help — Помощь")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    # Убрал parse_mode, чтобы не было ошибки 400 Bad Request
    help_text = (
        "🛰 ИНФОРМАЦИЯ И ПОМОЩЬ\n\n"
        f"🌐 Наш сайт: {WEB_URL}\n"
        "🛰 /get — Список быстрых прокси\n\n"
        "🛠 Поддержка: @Ovekin_777_bot\n"
        f"👑 Админ: @{ADMIN_USERNAME}"
        "🛠 НАШ ТГ КАНАЛ: https://t.me/proxy_timoxa\n"
    )
    bot.send_message(m.chat.id, help_text, disable_web_page_preview=True)

@bot.message_handler(commands=['get'])
def get_cmd(m):
    wait_msg = bot.send_message(m.chat.id, "🛰 Ищу лучшие варианты...")
    valid = get_fresh_proxies(6)
    if valid:
        res = "📡 АКТУАЛЬНЫЕ MTPROTO:\n\n"
        for p in valid:
            res += f"{p['icon']} {p['ms']}ms — {p['url']}\n\n"
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id)
    else:
        bot.edit_message_text("❌ Прокси не найдены, попробуйте позже.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        valid = get_fresh_proxies(5)
        if valid:
            post_text = "🛰 СВЕЖИЕ ПРОКСИ + WEB\n\n"
            for p in valid:
                post_text += f"{p['icon']} Пинг: {p['ms']}ms\n{p['url']}\n\n"
            post_text += f"🌐 Больше на сайте: {WEB_URL}"
            bot.send_message(CHANNEL_ID, post_text, disable_web_page_preview=True)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 ADMIN\nЮзеров: {len(users)}\n/post — Рассылка")

if __name__ == "__main__":
    if not TOKEN:
        print("Ошибка: TOKEN не найден в Environment Variables!")
    else:
        keep_alive()
        print("Бот успешно запущен...")
        bot.polling(none_stop=True)
