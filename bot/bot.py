# =================================================================
# ПРОЕКТ: PROXY HUNTER v14.3 - MULTI-THREADED MAX
# СТАТУС: ИСПРАВЛЕНЫ ЗАВИСАНИЯ (HELP ТЕПЕРЬ ЛЕТАЕТ)
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

TOKEN = '8764406808:AAESVgV_PKemfwMaN5bdwiH3rgtXeYyMYOs'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_TAG = "@Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa" 
LOG_CHANNEL_ID = "@logi_proxy" 
CHANNEL_LINK = "https://t.me/proxy_timoxa"
WEB_LINK = "https://proxy-rhe6.onrender.com"

# Глобальный кэш для прокси, чтобы /get работал мгновенно
proxy_cache = []
cache_lock = Lock()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота с поддержкой 100+ потоков
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=100)

# ---------------------------------------------------------
# [ РАЗДЕЛ 2: ЛОГИКА ПРОВЕРКИ И ИСТОЧНИКИ ]
# ---------------------------------------------------------

def check_subscription(user_id):
    """Моментальная проверка подписки"""
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return True

def validate_proxy(p_tuple):
    """Проверка прокси на скорость и тип секрета (для РФ)"""
    host, port, secret = p_tuple
    try:
        start_t = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.3)
        res = s.connect_ex((host, int(port)))
        s.close()
        
        if res == 0:
            ping = int((time.time() - start_t) * 1000)
            # Отсеиваем фейки и слишком медленные
            if ping < 70 or ping > 900: return None
            
            # Приоритет секретам с обходом блокировок (ee/dd)
            is_stealth = secret.startswith(('ee', 'dd'))
            icon = "🟢" if ping < 350 else "🟡" if ping < 600 else "🔴"
            
            return {
                'latency': ping,
                'icon': icon,
                'link': f"tg://proxy?server={host}&port={port}&secret={secret}",
                'ip': host,
                'is_stealth': is_stealth
            }
    except:
        return None

def update_proxy_engine():
    """Фоновый процесс обновления базы прокси каждые 10 минут"""
    global proxy_cache
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/Hookzof/free-proxies/main/mtproto.txt",
        "https://raw.githubusercontent.com/Proxy-List/Proxy-List/master/mtproto.txt",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2RayCollector/main/proxy/mtproto",
        "https://raw.githubusercontent.com/Moghadam7/MTProtoProxy/main/MTProtoProxy.txt",
        "https://raw.githubusercontent.com/Paimon-Genshin/MTProto-Collector/main/proxy.txt",
        "https://raw.githubusercontent.com/biplobsd/MTProto-Proxy-List/master/proxy.txt",
        "https://raw.githubusercontent.com/MuhammedKalkan/Telegram-MTProto-List/master/proxies.txt",
        "https://raw.githubusercontent.com/Ellion-Design/MTProto-Proxy-List/main/proxies.txt"
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
                tasks = [executor.submit(validate_proxy, p) for p in pool[:500]]
                for t in as_completed(tasks):
                    res = t.result()
                    if res: temp_valid.append(res)
            
            # Обновляем глобальный кэш
            with cache_lock:
                proxy_cache = sorted(temp_valid, key=lambda x: x['latency'])
            
            logger.info(f">>> База обновлена: {len(proxy_cache)} рабочих прокси.")
        except Exception as e:
            logger.error(f"Ошибка обновления базы: {e}")
        
        time.sleep(600) # Ждем 10 минут до следующего обновления

# ---------------------------------------------------------
# [ РАЗДЕЛ 3: ВЕБ-ИНТЕРФЕЙС ]
# ---------------------------------------------------------

app = Flask(__name__)

@app.route('/')
def web_index():
    with cache_lock:
        data = proxy_cache[:15]
    
    html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>PROXY HUNTER</title>
        <style>
            body { background: #0f172a; color: white; font-family: sans-serif; text-align: center; padding: 20px; }
            .card { max-width: 500px; margin: auto; background: #1e293b; padding: 20px; border-radius: 25px; border: 1px solid #38bdf8; }
            .item { background: #334155; margin: 10px 0; padding: 15px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center; }
            .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 15px; border-radius: 10px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1 style="color:#38bdf8;">🛰 PROXY HUNTER</h1>
            {% for p in proxies %}
            <div class="item">
                <div style="text-align:left"><b>{{p.icon}} {{p.latency}}ms</b><br><small>{{p.ip[:25]}}</small></div>
                <a href="{{p.link}}" class="btn">ВКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
            <button onclick="location.reload()" style="width:100%; padding:15px; margin-top:10px; border-radius:15px; background:#f59e0b; color:white; border:none; font-weight:bold;">ОБНОВИТЬ</button>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, proxies=data)

# ---------------------------------------------------------
# [ РАЗДЕЛ 4: ОБРАБОТЧИК КОМАНД (ФИКС HELP) ]
# ---------------------------------------------------------

@bot.message_handler(commands=['start', 'help', 'get', 'admin', 'post'])
def command_router(message):
    """
    Использование @bot.message_handler(commands=[...]) — самый надежный способ.
    Теперь каждая команда обрабатывается в своем потоке.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    cmd = message.text.split()[0][1:].lower() # Убираем слэш и берем команду

    # ПРОВЕРКА ПОДПИСКИ
    if not check_subscription(user_id):
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("🚀 Подписаться", url=CHANNEL_LINK))
        bot.send_message(chat_id, "⚠️ Сначала подпишись на канал!", reply_markup=kb)
        return

    # --- ОБРАБОТКА ---

    if cmd == 'start':
        bot.send_message(chat_id, "🦾 **PROXY HUNTER v14.3**\n\n🛰 /get — Список прокси\n❓ /help — Помощь", parse_mode="Markdown")

    elif cmd == 'help':
        # Теперь отвечает МГНОВЕННО
        help_text = (
            "🛰 **ИНФОРМАЦИЯ И ПОДДЕРЖКА**\n\n"
            f"🌐 **Наш сайт:** {WEB_LINK}\n"
            "🛰 **Описание:** Бот ищет прокси с обходом DPI (блокировок РФ).\n\n"
            f"🛠 **Тех. поддержка:** {SUPPORT_TAG}\n"
            f"👑 **Админ:** @{ADMIN_USERNAME}"
        )
        bot.send_message(chat_id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

    elif cmd == 'get':
        with cache_lock:
            current = proxy_cache[:6]
        
        if current:
            txt = "📡 **АКТУАЛЬНЫЕ MTPROTO ДЛЯ РФ:**\n\n"
            for p in current:
                txt += f"{p['icon']} **{p['latency']}ms** — [ПОДКЛЮЧИТЬ]({p['link']})\n\n"
            bot.send_message(chat_id, txt, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, "⏳ База обновляется, подождите 30 секунд...")

    elif cmd == 'admin' and message.from_user.username == ADMIN_USERNAME:
        bot.send_message(chat_id, "👑 Админ-панель: используй `/post` для канала.")

    elif cmd == 'post' and message.from_user.username == ADMIN_USERNAME:
        with cache_lock:
            items = proxy_cache[:5]
        if items:
            p_msg = "🛰 **СВЕЖИЙ ПАКЕТ ПРОКСИ ДЛЯ РФ**\n\n"
            for i in items:
                p_msg += f"{i['icon']} Пинг: **{i['latency']}ms**\n🔗 {i['url']}\n\n"
            p_msg += f"🌐 Весь список: {WEB_LINK}"
            bot.send_message(CHANNEL_ID, p_msg, parse_mode="Markdown", disable_web_page_preview=True)
            bot.send_message(chat_id, "✅ Пост отправлен!")

# ---------------------------------------------------------
# [ РАЗДЕЛ 5: ЗАПУСК ]
# ---------------------------------------------------------

if __name__ == "__main__":
    # 1. Запускаем фоновый движок обновления прокси
    Thread(target=update_proxy_engine, daemon=True).start()
    
    # 2. Запускаем телеграм бота
    def bot_loop():
        time.sleep(10)
        bot.polling(none_stop=True, interval=0, timeout=60)
    Thread(target=bot_loop, daemon=True).start()
    
    # 3. Запускаем сайт
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
