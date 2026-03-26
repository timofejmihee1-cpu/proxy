import telebot
import requests
import re
import time
import random
import socket
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

# --- [ ЛОГИКА ПРОВЕРКИ ПРОКСИ ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
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
    raw_list = []
    try:
        r = requests.get(sources[0], timeout=5)
        raw_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text)
    except: return []
    
    unique = list(set(raw_list))
    random.shuffle(unique)
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        results = list(executor.map(check_proxy, unique[:50]))
    
    return sorted([r for r in results if r], key=lambda x: x['ms'])[:limit]

# --- [ ВЕБ-САЙТ (БУДИЛЬНИК + ВИТРИНА) ] ---
app = Flask('')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Proxy Hunter Web</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 20px; }
        .container { max-width: 500px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 20px; box-shadow: 0 15px 30px rgba(0,0,0,0.4); border: 1px solid #334155; }
        h1 { color: #38bdf8; margin-bottom: 5px; }
        .proxy-card { background: #334155; margin: 12px 0; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
        .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 15px; border-radius: 8px; font-weight: bold; }
        .ping { font-weight: bold; font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰 PROXY HUNTER</h1>
        <p style="color: #94a3b8;">Если Telegram не работает, выбери прокси ниже:</p>
        <hr style="border: 0; border-top: 1px solid #475569; margin: 20px 0;">
        
        {% for p in proxies %}
        <div class="proxy-card">
            <div style="text-align: left;">
                <span class="ping">{{ p.icon }} {{ p.ms }}ms</span><br>
                <small style="font-size: 10px; color: #94a3b8;">{{ p.server[:20] }}...</small>
            </div>
            <a href="{{ p.url }}" class="btn">ВКЛЮЧИТЬ</a>
        </div>
        {% endfor %}

        <p style="font-size: 12px; color: #64748b; margin-top: 20px;">
            Создано Тимофеем | <a href="{{ support }}" style="color: #38bdf8; text-decoration: none;">Поддержка</a>
        </p>
    </div>
    <script>setTimeout(function(){ location.reload(); }, 60000);</script>
</body>
</html>
"""

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
    return render_template_string(HTML_TEMPLATE, proxies=proxies, support=SUPPORT_LINK)

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    text = (
        "🦾 **PROXY HUNTER v13.2**\n\n"
        "🛰 /get — Поиск быстрых прокси\n"
        "❓ /help — Важная информация"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "🛰 **Ищу лучшие варианты...**")
    valid = get_fresh_proxies(6)
    
    if valid:
        res = "📡 **АКТУАЛЬНЫЕ MTPROTO:**\n\n"
        for p in valid:
            res += f"{p['icon']} **{p['ms']}ms** — {p['url']}\n\n"
        
        res += (
            "⚠️ **ВНИМАНИЕ:**\n"
            "Некоторые прокси могут не работать из-за ограничений твоего **оператора** или **Wi-Fi**. Если не грузит — просто попробуй следующий из списка."
        )
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Нет доступных прокси. Попробуй /get еще раз.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = (
        "❓ **ИНФОРМАЦИЯ**\n\n"
        "🟢 — Пинг отличный\n"
        "🟡 — Пинг средний\n"
        "🔴 — Медленно\n\n"
        "🛑 **ПРОБЛЕМЫ?**\n"
        "Провайдеры интернета часто блокируют порты. Если прокси не подключается:\n"
        "— Попробуй сменить тип интернета (Wi-Fi/4G)\n"
        "— Выбери другой вариант в списке\n"
        "— Используй наш сайт: " + WEB_URL + "\n\n"
        "💡 **ЕСТЬ ИДЕЯ?**\n"
        "Мы всегда рады вашим предложениям! Пишите в нашу поддержку: [КЛИК СЮДА](" + SUPPORT_LINK + ")"
    )
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        wait_msg = bot.send_message(m.chat.id, "⏳ Формирую пост для канала...")
        valid = get_fresh_proxies(5)
        
        if valid:
            post_text = "🛰 **СВЕЖИЕ ПРОКСИ ДЛЯ ТЕЛЕГИ**\n\n"
            for p in valid:
                post_text += f"{p['icon']} Пинг: **{p['ms']}ms**\n{p['url']}\n\n"
            
            post_text += f"🌐 Наш сайт: {WEB_URL}\n"
            post_text += f"📢 Подпишись на {CHANNEL_ID}, чтобы не терять связь!"
            
            try:
                bot.send_message(CHANNEL_ID, post_text, disable_web_page_preview=True)
                bot.edit_message_text("✅ Опубликовано в канале!", m.chat.id, wait_msg.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Ошибка: {e}", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **ADMIN**\nЮзеров: {len(users)}\n/post — Пост в канал")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
