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

# --- [ НАСТРОЙКИ ] ---
TOKEN = '8764406808:AAF2jaeyaLtCYbufyxcNQ8u-jnGc33NrQOc'
ADMIN_USERNAME = "PR1SM_777" 
CHANNEL_ID = "@proxy_timoxa"

bot = telebot.TeleBot(TOKEN)
users = set()

# --- [ ПОИСК И ПРОВЕРКА ПРОКСИ ] ---
def check_proxy(p_data):
    if len(p_data) == 3:
        srv, prt, sec = p_data
        url = f"tg://proxy?server={srv}&port={prt}&secret={sec}"
    else:
        srv, prt = p_data
        url = f"tg://proxy?server={srv}&port={prt}&secret=ee00000000000000000000000000000000676f6f676c652e636f6d"

    try:
        start = time.time()
        # Быстрая проверка сокета (0.8 сек таймаут)
        sock = socket.create_connection((srv, int(prt)), timeout=0.8)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        if ms < 150: icon = "🟢"
        elif ms < 300: icon = "🟡"
        else: icon = "🔴"
            
        return {'ms': ms, 'icon': icon, 'url': url, 'server': srv}
    except: return None

def get_fresh_proxies(limit=8):
    # Берем сразу из нескольких источников, чтобы список никогда не был пустым
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
        "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt"
    ]
    
    all_raw = ""
    for s in sources:
        try:
            r = requests.get(s, timeout=5)
            all_raw += r.text + "\n"
        except: continue
    
    # Ищем все возможные форматы (MTProto и IP:PORT)
    mtp_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', all_raw)
    socks_list = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', all_raw)
    
    combined = list(set(mtp_list + socks_list))
    random.shuffle(combined)
    
    # Проверяем первые 80 штук в 35 потоков
    with ThreadPoolExecutor(max_workers=35) as executor:
        results = list(executor.map(check_proxy, combined[:80]))
    
    valid = sorted([r for r in results if r], key=lambda x: x['ms'])
    return valid[:limit]

# --- [ ВЕБ-СЕРВЕР ДЛЯ СТАРОГО ТЕЛЕФОНА ] ---
app = Flask('')

@app.route('/ping')
def ping():
    return "ALIVE", 200

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
    HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8"><title>Proxy Web</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: #0f172a; color: white; font-family: sans-serif; text-align: center; }
            .card { background: #1e293b; margin: 10px auto; padding: 15px; border-radius: 15px; max-width: 400px; border: 1px solid #334155; }
            .btn { background: #38bdf8; color: black; text-decoration: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🛰 PROXY HUNTER WEB</h1>
        {% for p in proxies %}
        <div class="card">
            <p>{{ p.icon }} Пинг: <b>{{ p.ms }}ms</b></p>
            <a href="{{ p.url }}" class="btn">ПОДКЛЮЧИТЬ</a>
        </div>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(HTML, proxies=proxies)

def run_web(): app.run(host='0.0.0.0', port=8080)

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    bot.send_message(m.chat.id, "🦾 **Бот активирован!**\n\n/get — Получить быстрые прокси\n/admin — Статистика")

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait = bot.send_message(m.chat.id, "🛰 **Ищу лучшие варианты (пингую серверы)...**")
    valid = get_fresh_proxies(6)
    if valid:
        res = "📡 **САМЫЕ БЫСТРЫЕ ПРОКСИ:**\n\n"
        for p in valid: res += f"{p['icon']} **{p['ms']}ms**\n`{p['url']}`\n\n"
        bot.edit_message_text(res, m.chat.id, wait.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Сейчас все прокси медленные. Попробуй через минуту!", m.chat.id, wait.message_id)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **АДМИН-ПАНЕЛЬ**\n\nВсего юзеров: {len(users)}\n/post — Рассылка в канал")

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        valid = get_fresh_proxies(5)
        if valid:
            text = "🛰 **СВЕЖАЯ ПАРТИЯ ПРОКСИ**\n\n"
            for p in valid: text += f"{p['icon']} Пинг: **{p['ms']}ms**\n{p['url']}\n\n"
            bot.send_message(CHANNEL_ID, text)

if __name__ == "__main__":
    # Запуск веб-сервера в отдельном потоке
    Thread(target=run_web).start()
    # Запуск бота
    print("Бот запущен...")
    bot.polling(none_stop=True)
