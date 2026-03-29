# =================================================================
# ПРОЕКТ: PROXY HUNTER v14.3 - FULL REPAIR
# СТАТУС: КОМАНДЫ ИСПРАВЛЕНЫ, ЗАВИСАНИЯ УБРАНЫ
# =================================================================

import telebot
import requests
import re
import time
import random
import socket
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template_string
from threading import Thread, Lock

# ---------------------------------------------------------
# [ РАЗДЕЛ 1: КОНФИГУРАЦИЯ ]
# ---------------------------------------------------------

# ВНИМАНИЕ: Смени токен в @BotFather, этот засвечен!
TOKEN = '8764406808:AAGksp-skBypDJemRA9gESpXECwUVXPbesU'

ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_TAG = "@Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa" 
CHANNEL_LINK = "https://t.me/proxy_timoxa"
WEB_LINK = "https://proxy-rhe6.onrender.com"

proxy_cache = []
cache_lock = Lock()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Использовать infinity_polling для стабильности на Render
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=50)

# ---------------------------------------------------------
# [ РАЗДЕЛ 2: ЛОГИКА ]
# ---------------------------------------------------------

def check_subscription(user_id):
    """Проверка подписки с обработкой исключений"""
    if str(user_id) == "ID_АДМИНА": return True # Можно добавить свой ID
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return True # Пропускаем, если ошибка API

def validate_proxy(p_tuple):
    host, port, secret = p_tuple
    try:
        start_t = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        res = s.connect_ex((host, int(port)))
        s.close()
        
        if res == 0:
            ping = int((time.time() - start_t) * 1000)
            if ping < 50 or ping > 1000: return None
            icon = "🟢" if ping < 400 else "🟡" if ping < 700 else "🔴"
            return {'latency': ping, 'icon': icon, 'link': f"tg://proxy?server={host}&port={port}&secret={secret}", 'ip': host}
    except:
        return None

def update_proxy_engine():
    global proxy_cache
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/Hookzof/free-proxies/main/mtproto.txt",
        "https://raw.githubusercontent.com/Proxy-List/Proxy-List/master/mtproto.txt",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2RayCollector/main/proxy/mtproto"
    ]
    while True:
        try:
            raw_data = []
            for url in sources:
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        raw_data.extend(re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text))
                except: continue
            
            pool = list(set(raw_data))
            random.shuffle(pool)
            
            temp_valid = []
            with ThreadPoolExecutor(max_workers=100) as executor:
                tasks = [executor.submit(validate_proxy, p) for p in pool[:400]]
                for t in as_completed(tasks):
                    res = t.result()
                    if res: temp_valid.append(res)
            
            with cache_lock:
                proxy_cache = sorted(temp_valid, key=lambda x: x['latency'])
            logger.info(f"Обновлено: {len(proxy_cache)} шт.")
        except Exception as e:
            logger.error(f"Ошибка движка: {e}")
        time.sleep(480)

# ---------------------------------------------------------
# [ РАЗДЕЛ 3: ВЕБ-ИНТЕРФЕЙС ]
# ---------------------------------------------------------

app = Flask(__name__)

@app.route('/')
def web_index():
    with cache_lock:
        data = proxy_cache[:20]
    html = """
    <body style="background:#0b0f19; color:white; font-family:sans-serif; text-align:center;">
        <h1 style="color:#3b82f6;">🛰 PROXY HUNTER ACTIVE</h1>
        <p>Бот работает в фоне. Доступно прокси: {{ count }}</p>
    </body>
    """
    return render_template_string(html, count=len(proxy_cache))

# ---------------------------------------------------------
# [ РАЗДЕЛ 4: ИСПРАВЛЕННЫЕ КОМАНДЫ ]
# ---------------------------------------------------------

@bot.message_handler(commands=['start'])
def send_start(message):
    bot.reply_to(message, "🦾 **PROXY HUNTER v14.3**\n\n🛰 /get — Список прокси\n❓ /help — Помощь", parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🛰 **ИНФОРМАЦИЯ И ПОМОЩЬ**\n\n"
        f"🌐 **Наш сайт:** {WEB_LINK}\n"
        "🛰 **Инфо:** Бот выдает прокси с обходом DPI (блокировок).\n\n"
        f"🛠 **Поддержка:** {SUPPORT_TAG}\n"
        f"👑 **Админ:** @{ADMIN_USERNAME}"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['get'])
def send_proxies(message):
    if not check_subscription(message.from_user.id):
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("🚀 Подписаться", url=CHANNEL_LINK))
        bot.send_message(message.chat.id, "⚠️ Подпишись на канал, чтобы использовать бота!", reply_markup=kb)
        return

    with cache_lock:
        current = proxy_cache[:8]
    
    if current:
        txt = "📡 **АКТУАЛЬНЫЕ MTPROTO:**\n\n"
        for p in current:
            txt += f"{p['icon']} **{p['latency']}ms** — [ПОДКЛЮЧИТЬ]({p['link']})\n\n"
        bot.send_message(message.chat.id, txt, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "⏳ База обновляется, подожди 30 секунд...")

@bot.message_handler(commands=['post'])
def admin_post(message):
    if message.from_user.username == ADMIN_USERNAME:
        with cache_lock:
            items = proxy_cache[:5]
        if items:
            p_msg = "🛰 **НОВЫЙ ПАКЕТ ПРОКСИ**\n\n"
            for i in items:
                p_msg += f"{i['icon']} Пинг: **{i['latency']}ms**\n🔗 {i['link']}\n\n"
            bot.send_message(CHANNEL_ID, p_msg, parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ Опубликовано!")

# ---------------------------------------------------------
# [ РАЗДЕЛ 5: ЗАПУСК ]
# ---------------------------------------------------------

def run_bot():
    # Используем infinity_polling для автоматического перезапуска при ошибках
    bot.infinity_polling(timeout=20, long_polling_timeout=5)

if __name__ == "__main__":
    # Запуск движка
    Thread(target=update_proxy_engine, daemon=True).start()
    
    # Запуск бота
    Thread(target=run_bot, daemon=True).start()
    
    # Запуск Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
