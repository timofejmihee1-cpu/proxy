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

# =========================================================
# [ БЛОК 1: ГЛОБАЛЬНАЯ КОНФИГУРАЦИЯ И НАСТРОЙКИ ]
# =========================================================
# Основные ключи доступа
TOKEN = '8764406808:AAESVgV_PKemfwMaN5bdwiH3rgtXeYyMYOs'

# Данные администратора и контакты
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 

# Настройки каналов (ID и Ссылки)
CHANNEL_ID = "@proxy_timoxa" 
LOG_CHANNEL_ID = "@logi_proxy" 
CHANNEL_URL = "https://t.me/proxy_timoxa"

# Ссылка на веб-интерфейс (Render)
WEB_URL = "https://proxy-rhe6.onrender.com"

# Инициализация бота с поддержкой 40 одновременных потоков
# Это нужно, чтобы бот не тормозил при большом наплыве юзеров
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=40)

# =========================================================
# [ БЛОК 2: ПРОВЕРКА ПОДПИСКИ (ОБЯЗАТЕЛЬНОЕ УСЛОВИЕ) ]
# =========================================================
def is_subscribed(user_id):
    """
    Проверяет статус пользователя в канале.
    Если бот не админ в канале, проверка всегда будет давать True.
    """
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        else:
            return False
    except Exception as e:
        # В случае ошибки API (например, канал не найден), пускаем пользователя
        print(f"Ошибка системы подписки: {e}")
        return True 

# =========================================================
# [ БЛОК 3: СИСТЕМА ДЕТАЛЬНОГО ЛОГИРОВАНИЯ ]
# =========================================================
def send_log(message):
    """
    Отправляет полный отчет о действиях пользователя в @logi_proxy
    """
    try:
        user = message.from_user
        first_name = user.first_name if user.first_name else "Без имени"
        username = f"@{user.username}" if user.username else "Нет юзернейма"
        user_id = user.id
        content = message.text if message.text else "[Медиа-контент]"
        
        log_report = "🚀 **ОТЧЕТ О ДЕЙСТВИИ ЮЗЕРА**\n"
        log_report += "--------------------------------------\n"
        log_report += f"👤 Имя: **{first_name}**\n"
        log_report += f"🔗 Юзер: {username}\n"
        log_report += f"🆔 ID: `{user_id}`\n"
        log_report += f"💬 Сообщение: {content}\n"
        log_report += "--------------------------------------"
        
        bot.send_message(LOG_CHANNEL_ID, log_report, parse_mode="Markdown")
    except Exception as e:
        print(f"Критическая ошибка логирования: {e}")

# =========================================================
# [ БЛОК 4: ИНТЕЛЛЕКТУАЛЬНЫЙ ЧЕКЕР ПРОКСИ ДЛЯ РФ ]
# =========================================================
def check_proxy_performance(proxy_data):
    """
    Проверяет прокси на доступность и фильтрует фейки для России.
    """
    server, port, secret = proxy_data
    try:
        start_timestamp = time.time()
        
        # Создаем сетевое соединение (TCP Socket)
        checker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        checker_socket.settimeout(1.0) # Увеличили таймаут для точности
        
        # Проверка порта
        connection_code = checker_socket.connect_ex((server, int(port)))
        checker_socket.close()
        
        if connection_code == 0:
            end_timestamp = time.time()
            # Вычисляем задержку в миллисекундах
            latency_ms = int((end_timestamp - start_timestamp) * 1000)
            
            # --- [ ЖЕСТКАЯ ФИЛЬТРАЦИЯ ДЛЯ РФ ] ---
            # 1. Отсекаем фейковые прокси с пингом ниже 120мс
            if latency_ms < 120:
                return None
            
            # 2. Отсекаем слишком лагающие (выше 800мс)
            if latency_ms > 800:
                return None
            
            # 3. Проверка на маскировку TLS (секреты ee... или dd...)
            # Эти прокси работают в России намного лучше остальных
            is_secure = secret.startswith(('ee', 'dd'))
            
            # Если секрет обычный, но пинг подозрительно низкий - скипаем
            if not is_secure and latency_ms < 200:
                return None

            # Присвоение статуса и иконки
            if latency_ms < 300:
                status_emoji = "🟢"
            elif latency_ms < 500:
                status_emoji = "🟡"
            else:
                status_emoji = "🔴"
                
            tg_proxy_url = f"tg://proxy?server={server}&port={port}&secret={secret}"
            
            return {
                'ping': latency_ms,
                'emoji': status_emoji,
                'link': tg_proxy_url,
                'host': server
            }
        else:
            return None
    except:
        return None

def fetch_and_filter_proxies(limit_count=8):
    """
    Собирает прокси из внешних баз и проводит многопоточный тест.
    """
    # Список надежных источников (GitHub)
    source_urls = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/Hookzof/free-proxies/main/mtproto.txt"
    ]
    
    raw_proxies_list = []
    
    try:
        for url in source_urls:
            response = requests.get(url, timeout=7)
            if response.status_code == 200:
                # Поиск всех совпадений по формату MTProto
                matches = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', response.text)
                raw_proxies_list.extend(matches)
        
        # Удаление дубликатов через set
        clean_list = list(set(raw_raw_proxies_list))
        random.shuffle(clean_list)
        
        final_verified = []
        
        # Используем ThreadPoolExecutor для мгновенной проверки 150 прокси одновременно
        with ThreadPoolExecutor(max_workers=60) as executor:
            # Запускаем чекер в 60 потоков
            test_results = list(executor.map(check_proxy_performance, clean_list[:150]))
            
        # Сбор только успешных результатов
        for result in test_results:
            if result is not None:
                final_verified.append(result)
                
        # Сортировка по возрастанию пинга (самые быстрые вверху)
        sorted_list = sorted(final_verified, key=lambda x: x['ping'])
        
        return sorted_list[:limit_count]
    except Exception as e:
        print(f"Ошибка загрузки базы прокси: {e}")
        return []

# =========================================================
# [ БЛОК 5: ВЕБ-ИНТЕРФЕЙС (FLASK SERVER) ]
# =========================================================
app = Flask(__name__)

@app.route('/status')
def status_page():
    return "SERVER IS RUNNING", 200

@app.route('/')
def main_web_interface():
    # Получаем 10 лучших прокси для сайта
    web_list = fetch_and_filter_proxies(10)
    
    # Полная верстка без сокращений
    html_template = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>PROXY HUNTER | OFFICIAL</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Arial, sans-serif; text-align: center; margin: 0; padding: 25px; }
            .main-container { max-width: 600px; margin: 0 auto; background-color: #1e293b; padding: 35px; border-radius: 30px; border: 1px solid #334155; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
            h1 { color: #38bdf8; font-size: 32px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 3px; }
            .sub-title { color: #94a3b8; font-size: 14px; margin-bottom: 35px; }
            .proxy-card { background-color: #334155; margin-bottom: 15px; padding: 20px; border-radius: 18px; display: flex; justify-content: space-between; align-items: center; transition: all 0.3s ease; border: 1px solid transparent; }
            .proxy-card:hover { border-color: #38bdf8; transform: translateY(-3px); }
            .info { text-align: left; }
            .ping-text { font-weight: bold; font-size: 20px; color: #f1f5f9; }
            .host-text { color: #64748b; font-size: 12px; display: block; margin-top: 4px; }
            .connect-button { background-color: #38bdf8; color: #0f172a; text-decoration: none; padding: 12px 25px; border-radius: 12px; font-weight: 800; font-size: 14px; transition: background 0.3s; }
            .connect-button:hover { background-color: #7dd3fc; }
            .refresh-btn { background-color: #f59e0b; color: white; border: none; padding: 18px 40px; border-radius: 15px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 25px; transition: opacity 0.3s; }
            .refresh-btn:hover { opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="main-container">
            <h1>🛰 PROXY HUNTER</h1>
            <div class="sub-title">ОПТИМИЗИРОВАНО ДЛЯ РОССИИ 🇷🇺</div>
            
            {% for p in proxy_items %}
            <div class="proxy-card">
                <div class="info">
                    <span class="ping-text">{{ p.emoji }} {{ p.ping }}ms</span>
                    <span class="host-text">{{ p.host[:30] }}</span>
                </div>
                <a href="{{ p.link }}" class="connect-button">ВКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
            
            <button onclick="location.reload()" class="refresh-btn">ОБНОВИТЬ СПИСОК</button>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, proxy_items=web_list)

# =========================================================
# [ БЛОК 6: ГЛАВНЫЙ ОБРАБОТЧИК ТЕЛЕГРАМ БОТА ]
# =========================================================
@bot.message_handler(func=lambda message: True)
def master_handler(message):
    # Логируем каждое входящее сообщение
    send_log(message)
    
    # Игнорируем сообщения без текста
    if message.text is None:
        return
        
    user_input = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Обработка только команд
    if user_input.startswith('/'):
        # 1. Сначала проверяем подписку на канал
        if is_subscribed(user_id) == False:
            markup = telebot.types.InlineKeyboardMarkup()
            sub_button = telebot.types.InlineKeyboardButton("🚀 Подписаться на канал", url=CHANNEL_URL)
            markup.add(sub_button)
            
            bot.send_message(
                chat_id, 
                "⚠️ **ОШИБКА ДОСТУПА!**\n\nЧтобы пользоваться ботом и получать рабочие прокси, вам нужно подписаться на наш официальный канал.", 
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
            
        # Определяем саму команду
        command_name = user_input.split()[0].lower()
        
        # --- [ КОМАНДА /START ] ---
        if command_name == '/start':
            start_text = "🦾 **WELCOME TO PROXY HUNTER v14.3**\n\n"
            start_text += "Я нахожу лучшие MTProto прокси, которые работают даже в условиях блокировок.\n\n"
            start_text += "🛰 /get — Получить список прокси\n"
            start_text += "❓ /help — Помощь и контакты"
            bot.send_message(chat_id, start_text, parse_mode="Markdown")
            
        # --- [ КОМАНДА /GET ] ---
        elif command_name == '/get':
            progress_msg = bot.send_message(chat_id, "🛰 **Запуск сканирования...**\nПроверяю узлы на доступность из РФ.")
            
            fresh_proxies = fetch_and_filter_proxies(6)
            
            if len(fresh_proxies) > 0:
                result_text = "📡 **АКТУАЛЬНЫЕ MTPROTO ДЛЯ РФ:**\n\n"
                for p in fresh_proxies:
                    result_text += f"{p['emoji']} **{p['ping']}ms** — [ПОДКЛЮЧИТЬ]({p['link']})\n\n"
                
                bot.edit_message_text(
                    text=result_text,
                    chat_id=chat_id,
                    message_id=progress_msg.message_id,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                bot.edit_message_text(
                    text="❌ **ПРОКСИ НЕ НАЙДЕНЫ**\nПопробуйте обновить список через минуту.",
                    chat_id=chat_id,
                    message_id=progress_msg.message_id
                )
                
        # --- [ КОМАНДА /HELP ] ---
        elif command_name == '/help':
            help_info = "🛰 **ИНФОРМАЦИЯ И ПОДДЕРЖКА**\n\n"
            help_info += f"🌐 Наш веб-сайт: {WEB_URL}\n"
            help_info += "🛰 Команда `/get` — выдает 6 самых быстрых прокси.\n\n"
            help_info += f"🛠 Тех. поддержка: @Ovekin_777_bot\n"
            help_info += f"👑 Владелец: @{ADMIN_USERNAME}"
            
            bot.send_message(chat_id, help_info, parse_mode="Markdown", disable_web_page_preview=True)

        # --- [ БЛОК АДМИНИСТРАТОРА ] ---
        elif command_name == '/admin':
            if message.from_user.username == ADMIN_USERNAME:
                admin_msg = "👑 **ПАНЕЛЬ УПРАВЛЕНИЯ АДМИНА**\n\n"
                admin_msg += "Используйте `/post`, чтобы опубликовать свежие прокси в канал."
                bot.send_message(chat_id, admin_msg, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, "❌ У вас нет прав доступа к этой команде.")

        elif command_name == '/post':
            if message.from_user.username == ADMIN_USERNAME:
                notif = bot.send_message(chat_id, "⏳ Подготовка публикации...")
                post_items = fetch_and_filter_proxies(5)
                
                if post_items:
                    post_content = "🛰 **СВЕЖИЙ ПАК РАБОЧИХ ПРОКСИ**\n\n"
                    for item in post_items:
                        post_content += f"{item['emoji']} Пинг: {item['ping']}ms\n🔗 {item['link']}\n\n"
                    
                    post_content += f"🌐 Весь список онлайн: {WEB_URL}"
                    
                    bot.send_message(CHANNEL_ID, post_content, parse_mode="Markdown", disable_web_page_preview=True)
                    bot.edit_message_text("✅ Пост успешно опубликован в канале!", chat_id, notif.message_id)
                else:
                    bot.edit_message_text("❌ Ошибка генерации пака.", chat_id, notif.message_id)

# =========================================================
# [ БЛОК 7: ЗАПУСК И ОБХОД ОГРАНИЧЕНИЙ RENDER ]
# =========================================================
def start_polling_process():
    """Запускает бота с задержкой, чтобы не конфликтовать с портами"""
    time.sleep(15) 
    print(">>> Telegram Bot активирован.")
    try:
        bot.polling(none_stop=True, interval=0, timeout=60)
    except Exception as e:
        print(f"Критический сбой бота: {e}")
        time.sleep(10)

if __name__ == "__main__":
    # 1. Запускаем бота в отдельном независимом потоке
    bot_system_thread = Thread(target=start_polling_process)
    bot_system_thread.daemon = True
    bot_system_thread.start()
    
    # 2. Определяем порт для Render
    render_port_env = os.environ.get("PORT", "8080")
    active_port = int(render_port_env)
    
    print(f">>> Запуск Flask-сервера на порту: {active_port}")
    
    # 3. Запускаем веб-часть в основном потоке
    try:
        # debug=False обязателен для работы в многопоточности на Render
        app.run(host='0.0.0.0', port=active_port, debug=False, use_reloader=False)
    except Exception as flask_error:
        print(f"Критический сбой веб-сервера: {flask_error}")
