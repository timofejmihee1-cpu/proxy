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
WEB_URL = "https://proxy-rhe6.onrender.com" # Твой сайт

bot = telebot.TeleBot(TOKEN)
users = set()

# --- [ ЛОГИКА ПРОВЕРКИ ПРОКСИ ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
        # Быстрая проверка соединения
        sock = socket.create_connection((srv, int(prt)), timeout=0.8)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        if ms < 150: icon = "🟢"
        elif ms < 300: icon = "🟡"
        else: icon = "🔴"
            
        return {'ms': ms, 'icon': icon, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}", 'server': srv}
    except: return None

def get_fresh_proxies(limit=8):
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/tgproxies.txt"
    ]
    raw_list = []
    for url in sources:
        try:
            r = requests.get(url, timeout=5)
            raw_list.extend(re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text))
        except: continue
    
    unique = list(set(raw_list))
    random.shuffle(unique)
    
    # Проверяем 40 штук для скорости
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_proxy, unique[:40]))
    
    return sorted([r for r in results if r], key=lambda x: x['ms'])[:limit]

# --- [ ВЕБ-САЙТ (FLASK) ] ---
app = Flask('')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Proxy Hunter Web</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; text-align: center; padding: 20px; margin: 0; }
        .container { max-width: 500px; margin: 20px auto; background: #1e293b; padding: 25px; border-radius: 20px; box-shadow: 0 15px 30px rgba(0,0,0,0.4); border: 1px solid #334155; }
        h1 { color: #38bdf8; font-size: 28px; margin-bottom: 10px; }
        .desc { color: #94a3b8; font-size: 15px; margin-bottom: 25px; line-height: 1.4; }
        .proxy-card { background: #334155; margin-bottom: 12px; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }
        .proxy-card:hover { background: #475569; }
        .info { text-align: left; }
        .ping { font-weight: bold; font-size: 16px; color: #fff; }
        .host { display: block; font-size: 11px; color: #94a3b8; margin-top: 4px; }
        .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; font-size: 14px; transition: 0.2s; }
        .btn:active { transform: scale(0.95); }
        .footer { margin-top: 30px; font-size: 13px; color: #64748b; }
        a { color: #38bdf8; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰 PROXY HUNTER</h1>
        <p class="desc">Если Telegram не подключается, выбери любой прокси ниже и нажми кнопку.</p>
        
        <div id="proxy-list">
            {% for p in proxies %}
            <div class="proxy-card">
                <div class="info">
                    <span class="ping">{{ p.icon }} {{ p.ms }}ms</span>
                    <span class="host">{{ p.server[:25] }}...</span>
                </div>
                <a href="{{ p.url }}" class="btn">ВКЛЮЧИТЬ</a>
            </div>
            {% else %}
                <p>Ищу активные прокси...<br>Пожалуйста, обновите страницу.</p>
            {% endfor %}
        </div>

        <div class="footer">
            Создано Тимофеем | <a href="{{ support }}">Поддержка</a><br>
            <small style="display:block; margin-top:10px;">Обновление каждые 60 сек</small>
        </div>
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
        "🦾 PROXY HUNTER v13.1\n\n"
        "🛰 /get — Список прокси в чат\n"
        f"🌐 {WEB_URL} — Наш сайт (если ТГ не грузит)\n"
        "❓ /help — Поддержка и помощь"
    )
    bot.send_message(m.chat.id, text)

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "🛰 Сканирую сеть...")
    valid = get_fresh_proxies(6)
    
    if valid:
        res = "📡 АКТУАЛЬНЫЕ MTPROTO:\n\n"
        for p in valid:
            res += f"{p['icon']} {p['ms']}ms — {p['url']}\n\n"
        res += f"🔗 Больше прокси на сайте: {WEB_URL}"
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id)
    else:
        bot.edit_message_text("❌ Прокси не найдены. Попробуй позже.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        wait_msg = bot.send_message(m.chat.id, "⏳ Формирую пост для канала...")
        valid = get_fresh_proxies(5)
        
        if valid:
            post_text = "🛰 ТОП БЫСТРЫХ ПРОКСИ\n\n"
            for p in valid:
                post_text += f"{p['icon']} Пинг: {p['ms']}ms\n{p['url']}\n\n"
            
            post_text += f"🌐 Наш сайт: {WEB_URL}\n"
            post_text += f"📢 Подпишись на {CHANNEL_ID}"
            
            try:
                bot.send_message(CHANNEL_ID, post_text, disable_web_page_preview=True)
                bot.edit_message_text("✅ Опубликовано в канале!", m.chat.id, wait_msg.message_id)
            except Exception as e:
                bot.edit_message_text(f"❌ Ошибка: {e}", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 АДМИН-ПАНЕЛЬ\n\nЮзеров: {len(users)}\n\nКоманды:\n/post — Сделать пост в канал\n/send — Рассылка")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    bot.send_message(m.chat.id, f"💡 Возникли вопросы? Пишите в поддержку: {SUPPORT_LINK}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
