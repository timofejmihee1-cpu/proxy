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
TOKEN = '8764406808:AAESVgV_PKemfwMaN5bdwiH3rgtXeYyMYOs'

ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa" 
LOG_CHANNEL_ID = "@logi_proxy" 
CHANNEL_URL = "https://t.me/proxy_timoxa"
WEB_URL = "https://proxy-rhe6.onrender.com"

# Включаем многопоточность для обработки очереди запросов
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=20)

# --- [ ЛОГИКА ПРОВЕРКИ ПОДПИСКИ ] ---
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status != 'left'
    except Exception as e:
        print(f"Ошибка подписки: {e}")
        return True 

# --- [ ЛОГИКА ЛОГИРОВАНИЯ ] ---
def send_log(message):
    try:
        user = message.from_user
        log_text = (
            f"👤 Юзер: {user.first_name} (@{user.username})\n"
            f"🆔 ID: {user.id}\n"
            f"💬 Текст: {message.text if message.text else '[Медиа/Кнопка]'}"
        )
        bot.send_message(LOG_CHANNEL_ID, log_text)
    except Exception as e:
        print(f"Ошибка лога: {e}")

# --- [ ОПТИМИЗИРОВАННЫЙ ЧЕКЕР ПРОКСИ ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
        # Таймаут 0.6 сек, чтобы отсеять медленные прокси для сайта
        sock = socket.create_connection((srv, int(prt)), timeout=0.6)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        if ms < 150: icon = "🟢"
        elif ms < 300: icon = "🟡"
        else: icon = "🔴"
            
        return {'ms': ms, 'icon': icon, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}", 'server': srv}
    except: return None

def get_fresh_proxies(limit=8):
    source = "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"
    try:
        r = requests.get(source, timeout=5)
        raw_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text)
        unique = list(set(raw_list))
        random.shuffle(unique)
        # Проверяем 80 штук одновременно для скорости
        with ThreadPoolExecutor(max_workers=40) as executor:
            results = list(executor.map(check_proxy, unique[:80]))
        valid = sorted([r for r in results if r], key=lambda x: x['ms'])
        return valid[:limit]
    except: return []

# --- [ ВЕБ-САЙТ (FLASK) ] ---
app = Flask(__name__)

@app.route('/ping')
def ping(): return "OK", 200

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Proxy Hunter Web</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: #0f172a; color: #f8fafc; font-family: -apple-system, sans-serif; text-align: center; padding: 20px; margin: 0; }
            .container { max-width: 500px; margin: 20px auto; background: #1e293b; padding: 25px; border-radius: 20px; border: 1px solid #334155; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
            h1 { color: #38bdf8; margin-bottom: 25px; }
            .proxy-card { background: #334155; margin-bottom: 12px; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
            .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 15px; border-radius: 8px; font-weight: bold; font-size: 14px; }
            .casino { margin-top: 25px; padding: 15px; border: 2px dashed #f59e0b; border-radius: 15px; }
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
            
        </div>
    </body>
    </html>
    """
    return render_template_string(HTML_TEMPLATE, proxies=proxies)

# --- [ ОБРАБОТЧИК СООБЩЕНИЙ БОТА ] ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(m):
    # Логируем каждое сообщение в @logi_proxy
    send_log(m)
    
    if not m.text: return

    if m.text.startswith('/'):
        # Проверка подписки для команд
        if not is_subscribed(m.from_user.id):
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🚀 Подписаться", url=CHANNEL_URL))
            bot.send_message(m.chat.id, "⚠️ Чтобы использовать бота, подпишись на наш канал!", reply_markup=markup)
            return

        cmd = m.text.split()[0].lower()
        
        if cmd == '/start':
            bot.send_message(m.chat.id, "🦾 PROXY HUNTER v14.3\n\n/get — Получить прокси\n/help — Информация")
        
        elif cmd == '/help':
            help_text = (
                "🛰 ИНФОРМАЦИЯ\n\n"
                f"🌐 Наш сайт: {WEB_URL}\n"
                "🛠 Поддержка: @Ovekin_777_bot\n"
                f"👑 Админ: @{ADMIN_USERNAME}"
            )
            bot.send_message(m.chat.id, help_text, disable_web_page_preview=True)
        
        elif cmd == '/get':
            msg = bot.send_message(m.chat.id, "🛰 Ищу лучшие прокси...")
            valid = get_fresh_proxies(6)
            if valid:
                res = "📡 ТВОИ MTPROTO ПРОКСИ:\n\n"
                for p in valid: res += f"{p['icon']} {p['ms']}ms — {p['url']}\n\n"
                bot.edit_message_text(res, m.chat.id, msg.message_id)
            else:
                bot.edit_message_text("❌ Прокси временно недоступны.", m.chat.id, msg.message_id)

        elif cmd == '/admin' and m.from_user.username == ADMIN_USERNAME:
            bot.send_message(m.chat.id, "👑 Админ-панель\n\n/post — Сделать рассылку в канал")

        elif cmd == '/post' and m.from_user.username == ADMIN_USERNAME:
            valid = get_fresh_proxies(5)
            if valid:
                post_text = "🛰 СВЕЖИЙ ПАК ПРОКСИ\n\n"
                for p in valid: post_text += f"{p['icon']} Пинг: {p['ms']}ms\n{p['url']}\n\n"
                post_text += f"🌐 Весь список: {WEB_URL}"
                bot.send_message(CHANNEL_ID, post_text, disable_web_page_preview=True)

# --- [ ЗАПУСК СИСТЕМЫ ] ---
def start_bot_polling():
    # Небольшая задержка, чтобы Flask успел занять порт и Render не выдал 502
    time.sleep(10)
    print("Запуск бота (polling)...")
    bot.polling(none_stop=True, skip_pending=True)

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=start_bot_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask на основном потоке (обязательно для Render)
    port = int(os.environ.get("PORT", 8080))
    print(f"Flask сервер стартует на порту {port}...")
    app.run(host='0.0.0.0', port=port)
