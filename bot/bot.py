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

# --- [ КОНФИГУРАЦИЯ СИСТЕМЫ ] ---
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
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=20)

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
            
        log_text = "👤 Информация о пользователе:\n"
        log_text += f"Имя: {first_name}\n"
        log_text += f"Username: @{username}\n"
        log_text += f"ID: {user_id}\n\n"
        log_text += f"💬 Сообщение: {text}"
        
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
        test_socket.settimeout(0.6)
        
        result = test_socket.connect_ex((server_address, int(port_number)))
        test_socket.close()
        
        if result == 0:
            end_time = time.time()
            latency = int((end_time - start_time) * 1000)
            
            # Выбор иконки в зависимости от задержки
            if latency < 150:
                status_icon = "🟢"
            elif latency < 300:
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
        
        # Поиск всех прокси по шаблону
        pattern = r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)'
        found_proxies = re.findall(pattern, content)
        
        # Убираем дубликаты и перемешиваем
        unique_proxies = list(set(found_proxies))
        random.shuffle(unique_proxies)
        
        final_list = []
        
        # Используем ThreadPool для быстрой проверки
        with ThreadPoolExecutor(max_workers=40) as executor:
            check_results = list(executor.map(check_proxy, unique_proxies[:80]))
            
        for item in check_results:
            if item is not None:
                final_list.append(item)
                
        # Сортировка по пингу
        sorted_proxies = sorted(final_list, key=lambda x: x['ms'])
        
        return sorted_proxies[:limit]
    except Exception as e:
        print(f"Ошибка получения прокси: {e}")
        return []

# ---------------------------------------------------------
# [ ВЕБ-ИНТЕРФЕЙС (FLASK) ]
# ---------------------------------------------------------
app = Flask(__name__)

@app.route('/health')
def health_check():
    return "Статус: Работает", 200

@app.route('/')
def index_page():
    # Получаем список прокси для сайта
    proxy_data = get_fresh_proxies(10)
    
    # HTML код страницы
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>PROXY HUNTER WEB</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                margin: 0;
                padding: 20px;
            }
            .main-container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #1e293b;
                padding: 30px;
                border-radius: 25px;
                border: 1px solid #334155;
                box-shadow: 0 15px 35px rgba(0,0,0,0.4);
            }
            h1 {
                color: #38bdf8;
                font-size: 28px;
                margin-bottom: 30px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            .proxy-item {
                background-color: #334155;
                margin-bottom: 15px;
                padding: 18px;
                border-radius: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: transform 0.2s;
            }
            .proxy-item:hover {
                transform: scale(1.02);
            }
            .info-block {
                text-align: left;
            }
            .ping-val {
                font-weight: bold;
                font-size: 18px;
            }
            .server-addr {
                color: #94a3b8;
                font-size: 12px;
            }
            .action-button {
                background-color: #38bdf8;
                color: #0f172a;
                text-decoration: none;
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: bold;
                transition: background 0.3s;
            }
            .action-button:hover {
                background-color: #7dd3fc;
            }
            .refresh-section {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #334155;
            }
            .update-btn {
                background-color: #f59e0b;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="main-container">
            <h1>🛰 PROXY HUNTER</h1>
            
            {% for proxy in proxies %}
            <div class="proxy-item">
                <div class="info-block">
                    <span class="ping-val">{{ proxy.icon }} {{ proxy.ms }}ms</span><br>
                    <span class="server-addr">{{ proxy.server[:25] }}</span>
                </div>
                <a href="{{ proxy.url }}" class="action-button">ПОДКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
            
            <div class="refresh-section">
                <button onclick="location.reload()" class="update-btn">ОБНОВИТЬ СПИСОК</button>
            </div>
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
    # Отправляем лог каждого сообщения
    send_log(message)
    
    if message.text is None:
        return
        
    user_text = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if user_text.startswith('/'):
        # Проверка обязательной подписки
        if is_subscribed(user_id) == False:
            keyboard = telebot.types.InlineKeyboardMarkup()
            sub_btn = telebot.types.InlineKeyboardButton("🚀 Подписаться", url=CHANNEL_URL)
            keyboard.add(sub_btn)
            
            bot.send_message(
                chat_id, 
                "⚠️ Чтобы использовать бота, подпишись на наш канал!", 
                reply_markup=keyboard
            )
            return
            
        command = user_text.split()[0].lower()
        
        # --- [ Команда /start ] ---
        if command == '/start':
            welcome_msg = "🦾 PROXY HUNTER v14.3\n\n"
            welcome_msg += "/get — Получить прокси\n"
            welcome_msg += "/help — Помощь"
            bot.send_message(chat_id, welcome_msg)
            
        # --- [ Команда /get ] ---
        elif command == '/get':
            waiting_msg = bot.send_message(chat_id, "🛰 Ищу лучшие прокси...")
            
            fresh_list = get_fresh_proxies(6)
            
            if len(fresh_list) > 0:
                response_text = "📡 АКТУАЛЬНЫЕ MTPROTO:\n\n"
                for p in fresh_list:
                    response_text += f"{p['icon']} {p['ms']}ms — {p['url']}\n\n"
                
                bot.edit_message_text(
                    text=response_text,
                    chat_id=chat_id,
                    message_id=waiting_msg.message_id,
                    disable_web_page_preview=True
                )
            else:
                bot.edit_message_text(
                    text="❌ Прокси временно недоступны. Попробуйте позже.",
                    chat_id=chat_id,
                    message_id=waiting_msg.message_id
                )
                
        # --- [ Команда /help ] ---
        elif command == '/help':
            help_msg = "🛰 ИНФОРМАЦИЯ И ПОМОЩЬ\n\n"
            help_msg += f"🌐 Наш сайт: {WEB_URL}\n"
            help_msg += "🛰 /get — Список быстрых прокси\n\n"
            help_msg += f"🛠 Поддержка: @Ovekin_777_bot\n"
            help_msg += f"👑 Админ: @{ADMIN_USERNAME}"
            
            bot.send_message(chat_id, help_msg, disable_web_page_preview=True)

        # --- [ Админ-команды ] ---
        elif command == '/admin':
            if message.from_user.username == ADMIN_USERNAME:
                bot.send_message(chat_id, "👑 Доступ разрешен.\n\nКоманды:\n/post — Рассылка")
            else:
                bot.send_message(chat_id, "❌ У вас нет прав доступа.")

        elif command == '/post':
            if message.from_user.username == ADMIN_USERNAME:
                bot_msg = bot.send_message(chat_id, "⏳ Генерирую пост...")
                post_proxies = get_fresh_proxies(5)
                
                if post_proxies:
                    p_text = "🛰 СВЕЖИЙ ПАК ПРОКСИ\n\n"
                    for prx in post_proxies:
                        p_text += f"{prx['icon']} Пинг: {prx['ms']}ms\n{prx['url']}\n\n"
                    
                    p_text += f"🌐 Весь список: {WEB_URL}"
                    bot.send_message(CHANNEL_ID, p_text, disable_web_page_preview=True)
                    bot.edit_message_text("✅ Пост опубликован!", chat_id, bot_msg.message_id)
                else:
                    bot.edit_message_text("❌ Ошибка при создании поста.", chat_id, bot_msg.message_id)

# ---------------------------------------------------------
# [ ЗАПУСК ВСЕЙ СИСТЕМЫ ]
# ---------------------------------------------------------
def start_telegram_bot():
    # Задержка для предотвращения конфликтов при старте на Render
    time.sleep(12)
    print(">>> Telegram Bot запущен.")
    try:
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Критическая ошибка бота: {e}")
        time.sleep(5)

if __name__ == "__main__":
    # 1. Создаем отдельный поток для работы бота
    bot_thread = Thread(target=start_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # 2. Определяем порт для Render
    environment_port = os.environ.get("PORT", "8080")
    current_port = int(environment_port)
    
    print(f">>> Flask запуск на порту: {current_port}")
    
    # 3. Запускаем веб-сервер в основном потоке
    try:
        app.run(host='0.0.0.0', port=current_port, debug=False, use_reloader=False)
    except Exception as flask_error:
        print(f"Ошибка Flask: {flask_error}")
