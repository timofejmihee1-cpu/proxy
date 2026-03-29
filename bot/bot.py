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

# --- [ ПОЛНАЯ КОНФИГУРАЦИЯ СИСТЕМЫ ] ---
TOKEN = '8764406808:AAESVgV_PKemfwMaN5bdwiH3rgtXeYyMYOs'

# Данные администратора
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 

# Каналы
CHANNEL_ID = "@proxy_timoxa" 
LOG_CHANNEL_ID = "@logi_proxy" 
CHANNEL_URL = "https://t.me/proxy_timoxa"

# Веб-адрес
WEB_URL = "https://proxy-rhe6.onrender.com"

# Инициализация бота с поддержкой потоков
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=25)

# ---------------------------------------------------------
# [ БЛОК ПРОВЕРКИ ПОДПИСКИ ]
# ---------------------------------------------------------
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        if status == 'left':
            return False
        else:
            return True
    except Exception as e:
        print(f"Ошибка при проверке подписки: {e}")
        return True 

# ---------------------------------------------------------
# [ БЛОК ЛОГИРОВАНИЯ В КАНАЛ ]
# ---------------------------------------------------------
def send_log(message):
    try:
        user = message.from_user
        first_name = user.first_name
        username = user.username
        user_id = user.id
        text = message.text
        
        if text is None:
            text = "[Действие или Медиа]"
            
        log_text = "🚀 НОВОЕ СООБЩЕНИЕ В БОТЕ\n"
        log_text += "--------------------------\n"
        log_text += f"👤 Имя: {first_name}\n"
        log_text += f"🔗 Юзер: @{username}\n"
        log_text += f"🆔 ID: {user_id}\n"
        log_text += f"💬 Текст: {text}\n"
        log_text += "--------------------------"
        
        bot.send_message(LOG_CHANNEL_ID, log_text)
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# ---------------------------------------------------------
# [ БЛОК РАБОТЫ С ПРОКСИ ]
# ---------------------------------------------------------
def check_proxy(p_data):
    server_address, port_number, secret_key = p_data
    try:
        start_time = time.time()
        
        # Создаем сокет для проверки соединения
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(0.8) # Чуть увеличили таймаут для стабильности
        
        result = test_socket.connect_ex((server_address, int(port_number)))
        test_socket.close()
        
        if result == 0:
            end_time = time.time()
            latency = int((end_time - start_time) * 1000)
            
            # --- ФИЛЬТР: Пропускаем только если пинг БОЛЬШЕ 100ms ---
            if latency < 100:
                return None
            
            # Верхний порог, чтобы не выдавать совсем дохлые
            if latency > 800:
                return None
            
            # Выбор иконки (теперь 🟢 это хороший рабочий пинг от 100)
            if latency < 250:
                status_icon = "🟢"
            elif latency < 450:
                status_icon = "🟡"
            else:
                status_icon = "🔴"
                
            proxy_link = f"tg://proxy?server={server_address}&port={port_number}&secret={secret_key}"
            
            return {
                'ms': latency,
                'icon': status_icon,
                'url': proxy_link,
                'server': server_address
            }
        else:
            return None
    except:
        return None

def get_fresh_proxies(limit=8):
    data_url = "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"
    try:
        response = requests.get(data_url, timeout=5)
        content = response.text
        
        pattern = r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)'
        found_proxies = re.findall(pattern, content)
        
        unique_proxies = list(set(found_proxies))
        random.shuffle(unique_proxies)
        
        final_list = []
        
        # Оптимизация: проверяем больше штук, так как фильтр от 100ms отсеет многих
        with ThreadPoolExecutor(max_workers=50) as executor:
            check_results = list(executor.map(check_proxy, unique_proxies[:120]))
            
        for item in check_results:
            if item is not None:
                final_list.append(item)
                
        # Сортировка: сначала те, что ближе к 100ms (самые быстрые из рабочих)
        sorted_proxies = sorted(final_list, key=lambda x: x['ms'])
        
        return sorted_proxies[:limit]
    except Exception as e:
        print(f"Ошибка получения прокси: {e}")
        return []

# ---------------------------------------------------------
# [ ВЕБ-ИНТЕРФЕЙС (FLASK) ]
# ---------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def index_page():
    proxy_data = get_fresh_proxies(10)
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>PROXY HUNTER WEB</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background-color: #0f172a; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 20px; margin: 0; }
            .main-container { max-width: 550px; margin: 0 auto; background-color: #1e293b; padding: 25px; border-radius: 20px; border: 1px solid #334155; }
            h1 { color: #38bdf8; margin-bottom: 25px; }
            .proxy-item { background-color: #334155; margin-bottom: 12px; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
            .action-button { background-color: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 15px; border-radius: 10px; font-weight: bold; }
            .update-btn { background-color: #f59e0b; color: white; border: none; padding: 15px 25px; border-radius: 12px; font-weight: bold; cursor: pointer; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="main-container">
            <h1>🛰 PROXY HUNTER</h1>
            {% for proxy in proxies %}
            <div class="proxy-item">
                <div style="text-align:left">
                    <span style="font-weight:bold;">{{ proxy.icon }} {{ proxy.ms }}ms</span><br>
                    <small style="color:#94a3b8;">{{ proxy.server[:25] }}</small>
                </div>
                <a href="{{ proxy.url }}" class="action-button">ПОДКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
            <button onclick="location.reload()" class="update-btn">ОБНОВИТЬ СПИСОК</button>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_content, proxies=proxy_data)

# ---------------------------------------------------------
# [ ОСНОВНОЙ ОБРАБОТЧИК БОТА ]
# ---------------------------------------------------------
@bot.message_handler(func=lambda m: True)
def main_handler(message):
    send_log(message)
    
    if message.text is None: return
    user_text = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if user_text.startswith('/'):
        if is_subscribed(user_id) == False:
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton("🚀 Подписаться", url=CHANNEL_URL))
            bot.send_message(chat_id, "⚠️ Чтобы использовать бота, подпишись на наш канал!", reply_markup=keyboard)
            return
            
        command = user_text.split()[0].lower()
        
        if command == '/start':
            welcome_msg = "🦾 PROXY HUNTER v14.3\n\n/get — Получить прокси\n/help — Помощь"
            bot.send_message(chat_id, welcome_msg)
            
        elif command == '/get':
            waiting_msg = bot.send_message(chat_id, "🛰 Ищу лучшие прокси...")
            fresh_list = get_fresh_proxies(6)
            
            if len(fresh_list) > 0:
                response_text = "📡 АКТУАЛЬНЫЕ MTPROTO:\n\n"
                for p in fresh_list:
                    response_text += f"{p['icon']} {p['ms']}ms — {p['url']}\n\n"
                bot.edit_message_text(response_text, chat_id, waiting_msg.message_id, disable_web_page_preview=True)
            else:
                bot.edit_message_text("❌ Прокси временно недоступны. Попробуйте позже.", chat_id, waiting_msg.message_id)
                
        elif command == '/help':
            help_msg = "🛰 ИНФОРМАЦИЯ И ПОМОЩЬ\n\n"
            help_msg += f"🌐 Наш сайт: {WEB_URL}\n"
            help_msg += "🛰 /get — Список быстрых прокси\n\n"
            help_msg += f"🛠 Поддержка: @Ovekin_777_bot\n"
            help_msg += f"👑 Админ: @{ADMIN_USERNAME}"
            bot.send_message(chat_id, help_msg, disable_web_page_preview=True)

        elif command == '/post' and message.from_user.username == ADMIN_USERNAME:
            post_proxies = get_fresh_proxies(5)
            if post_proxies:
                p_text = "🛰 СВЕЖИЙ ПАК ПРОКСИ\n\n"
                for prx in post_proxies:
                    p_text += f"{prx['icon']} Пинг: {prx['ms']}ms\n{prx['url']}\n\n"
                p_text += f"🌐 Весь список: {WEB_URL}"
                bot.send_message(CHANNEL_ID, p_text, disable_web_page_preview=True)

# ---------------------------------------------------------
# [ ЗАПУСК ВСЕЙ СИСТЕМЫ ]
# ---------------------------------------------------------
def start_telegram_bot():
    time.sleep(15) # Оптимизация для Render
    print(">>> Бот запущен.")
    bot.polling(none_stop=True, interval=0, timeout=40)

if __name__ == "__main__":
    bot_thread = Thread(target=start_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
