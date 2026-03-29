# =================================================================
# ПРOЕКТ: PROXY HUNTER v14.3 - MAXIMUM EDITION
# ОСОБЕННОСТИ: Оптимизация под РФ, Многопоточность, Веб-интерфейс
# =================================================================

import telebot
import requests
import re
import time
import random
import socket
import json
import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template_string
from threading import Thread

# ---------------------------------------------------------
# [ РАЗДЕЛ 1: ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ И НАСТРОЙКИ ]
# ---------------------------------------------------------

# Токен бота (Telegram Bot API)
BOT_TOKEN = '8764406808:AAESVgV_PKemfwMaN5bdwiH3rgtXeYyMYOs'

# Данные администратора
ADMIN_NICKNAME = "PR1SM_777" 
SUPPORT_USER = "@Ovekin_777_bot" 

# Идентификаторы каналов
PRIMARY_CHANNEL = "@proxy_timoxa"      # Канал для постов
LOG_COLLECTOR_CHANNEL = "@logi_proxy" # Канал для логов
SUBSCRIPTION_LINK = "https://t.me/proxy_timoxa"

# Ссылка на веб-хостинг Render
PROJECT_WEB_LINK = "https://proxy-rhe6.onrender.com"

# Настройка логирования в консоль для отладки на Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация объекта бота с поддержкой высокого количества потоков
# threaded=True позволяет обрабатывать запросы от сотен юзеров одновременно
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=50)

# ---------------------------------------------------------
# [ РАЗДЕЛ 2: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ПРОВЕРКИ ]
# ---------------------------------------------------------

def check_user_subscription(user_id_to_check):
    """
    Функция для проверки наличия пользователя в основном канале.
    Возвращает True, если пользователь подписан, и False в противном случае.
    """
    try:
        # Запрос к API Telegram для получения статуса участника
        member_info = bot.get_chat_member(PRIMARY_CHANNEL, user_id_to_check)
        
        # Список статусов, которые считаются "подписанными"
        valid_statuses = ['member', 'administrator', 'creator']
        
        if member_info.status in valid_statuses:
            return True
        else:
            return False
            
    except Exception as subscription_error:
        # В случае ошибки (например, если бот не админ в канале), пускаем юзера
        logger.error(f"Критическая ошибка проверки подписки: {subscription_error}")
        return True 

def send_detailed_log(message_object):
    """
    Формирует и отправляет расширенный лог действий пользователя в канал логов.
    Включает имя, юзернейм, ID и текст сообщения.
    """
    try:
        user_data = message_object.from_user
        
        # Сбор данных о пользователе
        name_of_user = user_data.first_name if user_data.first_name else "Имя скрыто"
        tag_of_user = f"@{user_data.username}" if user_data.username else "Юзернейм отсутствует"
        unique_id = user_data.id
        raw_text = message_object.text if message_object.text else "[Медиа-файл или кнопка]"
        
        # Формирование текста лога
        log_payload = "📋 **ОТЧЕТ О СОБЫТИИ**\n"
        log_payload += "━━━━━━━━━━━━━━━━━━━━━━\n"
        log_payload += f"👤 **Пользователь:** {name_of_user}\n"
        log_payload += f"🔗 **Тег:** {tag_of_user}\n"
        log_payload += f"🆔 **ID:** `{unique_id}`\n"
        log_payload += f"💬 **Сообщение:** {raw_text}\n"
        log_payload += "━━━━━━━━━━━━━━━━━━━━━━"
        
        bot.send_message(LOG_COLLECTOR_CHANNEL, log_payload, parse_mode="Markdown")
        
    except Exception as log_dispatch_error:
        logger.error(f"Ошибка при отправке лога в канал: {log_dispatch_error}")

# ---------------------------------------------------------
# [ РАЗДЕЛ 3: ЯДРО СИСТЕМЫ ПРОВЕРКИ ПРОКСИ ]
# ---------------------------------------------------------

def validate_proxy_node(proxy_tuple, use_strict_filter=True):
    """
    Проверяет работоспособность прокси через создание прямого сокета.
    Использует адаптивные фильтры для обхода ограничений в России.
    """
    target_server, target_port, target_secret = proxy_tuple
    
    try:
        # Засекаем время начала проверки для расчета пинга
        start_check_time = time.time()
        
        # Инициализация TCP сокета
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Установка таймаута (чуть больше для стабильного обнаружения в РФ)
        test_socket.settimeout(1.3)
        
        # Попытка подключения к порту
        connection_status = test_socket.connect_ex((target_server, int(target_port)))
        test_socket.close()
        
        # Если порт открыт (код 0)
        if connection_status == 0:
            end_check_time = time.time()
            final_latency = int((end_check_time - start_check_time) * 1000)
            
            # --- ПРИМЕНЕНИЕ ФИЛЬТРОВ ДЛЯ РФ ---
            if use_strict_filter:
                # 1. Защита от фейковых быстрых прокси (заглушек)
                if final_latency < 115:
                    return None
                
                # 2. Ограничение по верхнему порогу для комфортной работы
                if final_latency > 850:
                    return None
                
                # 3. Проверка на поддержку TLS маскировки (dd/ee секреты)
                # Это критически важно для обхода Deep Packet Inspection (DPI)
                is_secure_secret = target_secret.startswith(('ee', 'dd'))
                
                if not is_secure_secret and final_latency < 200:
                    # Обычные секреты с очень низким пингом часто блокируются в РФ
                    return None
            else:
                # Мягкий режим: если в строгом режиме ничего не нашлось
                if final_latency < 60 or final_latency > 1500:
                    return None

            # Вычисление иконки качества (Emoji Indicator)
            if final_latency < 350:
                quality_emoji = "🟢"
            elif final_latency < 550:
                quality_emoji = "🟡"
            else:
                quality_emoji = "🔴"
                
            # Сборка финального словаря данных прокси
            return {
                'ping_val': final_latency,
                'visual': quality_emoji,
                'connection_url': f"tg://proxy?server={target_server}&port={target_port}&secret={target_secret}",
                'ip_address': target_server
            }
        else:
            return None
            
    except Exception:
        # Ошибки сокета игнорируем, просто считаем прокси мертвым
        return None

def master_proxy_fetcher(max_results=8):
    """
    Основной агрегатор прокси. Собирает данные, фильтрует и возвращает лучшие.
    """
    # Список надежных источников с GitHub (MTProto базы)
    database_urls = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/Hookzof/free-proxies/main/mtproto.txt",
        "https://raw.githubusercontent.com/Proxy-List/Proxy-List/master/mtproto.txt",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2RayCollector/main/proxy/mtproto"
    ]
    
    aggregated_raw_data = []
    
    try:
        # Сбор сырых данных из всех источников
        for current_url in database_urls:
            response_data = requests.get(current_url, timeout=12)
            if response_data.status_code == 200:
                # Регулярное выражение для парсинга параметров прокси
                extracted = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', response_data.text)
                aggregated_raw_data.extend(extracted)
        
        # Очистка от дубликатов
        unique_proxy_set = list(set(aggregated_raw_data))
        random.shuffle(unique_proxy_set)
        
        final_valid_list = []
        
        # --- ИТЕРАЦИЯ 1: СТРОГИЙ ПОИСК (ОПТИМАЛЬНО ДЛЯ РФ) ---
        # Используем ThreadPoolExecutor для параллельной проверки 80 прокси сразу
        with ThreadPoolExecutor(max_workers=80) as master_executor:
            # Маппинг функции проверки на список прокси
            task_futures = [master_executor.submit(validate_proxy_node, p, True) for p in unique_proxy_set[:250]]
            
            for finished_task in as_completed(task_futures):
                result_node = finished_task.result()
                if result_node is not None:
                    final_valid_list.append(result_node)
        
        # --- ИТЕРАЦИЯ 2: АДАПТИВНЫЙ ПОИСК (ЕСЛИ МАЛО РЕЗУЛЬТАТОВ) ---
        if len(final_valid_list) < 3:
            with ThreadPoolExecutor(max_workers=80) as backup_executor:
                backup_futures = [backup_executor.submit(validate_proxy_node, p, False) for p in unique_proxy_set[:200]]
                for finished_backup in as_completed(backup_futures):
                    backup_node = finished_backup.result()
                    if backup_node is not None:
                        final_valid_list.append(backup_node)
        
        # Сортировка по возрастанию пинга (самые быстрые в топе)
        sorted_results = sorted(final_valid_list, key=lambda x: x['ping_val'])
        
        # Возвращаем нужное количество прокси
        return sorted_results[:max_results]
        
    except Exception as fetch_error:
        logger.error(f"Ошибка в мастер-загрузчике: {fetch_error}")
        return []

# ---------------------------------------------------------
# [ РАЗДЕЛ 4: ВЕБ-СЕРВЕР (FLASK) ДЛЯ МОНИТОРИНГА ]
# ---------------------------------------------------------

app = Flask(__name__)

# HTML шаблон для веб-страницы (максимально проработанный)
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>PROXY HUNTER WEB v14.3</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 30px; min-height: 100vh; }
        .wrapper { max-width: 600px; margin: 0 auto; background: rgba(30, 41, 59, 0.8); padding: 40px; border-radius: 35px; border: 1px solid rgba(56, 189, 248, 0.2); backdrop-filter: blur(10px); }
        h1 { color: #38bdf8; font-size: 36px; margin-bottom: 5px; text-shadow: 0 0 20px rgba(56, 189, 248, 0.4); }
        .status-badge { display: inline-block; background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 5px 15px; border-radius: 20px; font-size: 12px; margin-bottom: 30px; font-weight: bold; }
        .proxy-container { display: flex; flex-direction: column; gap: 15px; }
        .proxy-item { background: rgba(51, 65, 85, 0.6); padding: 20px; border-radius: 20px; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; transition: 0.3s; }
        .proxy-item:hover { transform: scale(1.02); border-color: #38bdf8; background: rgba(51, 65, 85, 0.9); }
        .proxy-info { text-align: left; }
        .ping-label { font-size: 22px; font-weight: bold; }
        .host-label { font-size: 11px; color: #94a3b8; display: block; margin-top: 5px; }
        .action-link { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 12px 25px; border-radius: 12px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3); }
        .refresh-button { background: #f59e0b; color: white; border: none; padding: 20px; width: 100%; border-radius: 20px; font-size: 18px; font-weight: bold; cursor: pointer; margin-top: 30px; transition: 0.3s; }
        .refresh-button:hover { background: #fbbf24; box-shadow: 0 0 20px rgba(245, 158, 11, 0.4); }
    </style>
</head>
<body>
    <div class="wrapper">
        <h1>🛰 PROXY HUNTER</h1>
        <div class="status-badge">OPTIMIZED FOR RUSSIA 🇷🇺</div>
        
        <div class="proxy-container">
            {% for item in list_of_proxies %}
            <div class="proxy-item">
                <div class="proxy-info">
                    <span class="ping-label">{{ item.visual }} {{ item.ping_val }}ms</span>
                    <span class="host-label">{{ item.ip_address[:30] }}</span>
                </div>
                <a href="{{ item.connection_url }}" class="action-link">ПОДКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
        </div>
        
        <button onclick="location.reload()" class="refresh-button">ОБНОВИТЬ СПИСОК</button>
    </div>
</body>
</html>
"""

@app.route('/')
def render_main_page():
    """Эндпоинт для отображения веб-интерфейса"""
    current_proxies = master_proxy_fetcher(12)
    return render_template_string(HTML_LAYOUT, list_of_proxies=current_proxies)

# ---------------------------------------------------------
# [ РАЗДЕЛ 5: ОБРАБОТЧИК КОМАНД ТЕЛЕГРАМ БОТА ]
# ---------------------------------------------------------

@bot.message_handler(func=lambda msg: True)
def main_telegram_handler(msg):
    """
    Главный диспетчер всех входящих сообщений бота.
    """
    # 1. Логируем действие в канал логов
    send_detailed_log(msg)
    
    # Игнорируем сообщения без текстового контента
    if not msg.text:
        return
        
    input_text = msg.text
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    
    # Обработка только если сообщение начинается со слэша (команда)
    if input_text.startswith('/'):
        
        # А) ПРОВЕРКА ПОДПИСКИ (Критически важный блок)
        is_user_valid = check_user_subscription(user_id)
        
        if not is_user_valid:
            # Создаем кнопку для подписки
            sub_keyboard = telebot.types.InlineKeyboardMarkup()
            btn_sub = telebot.types.InlineKeyboardButton("🚀 Подписаться на канал", url=SUBSCRIPTION_LINK)
            sub_keyboard.add(btn_sub)
            
            rejection_text = "⚠️ **ДОСТУП ЗАБЛОКИРОВАН**\n\n"
            rejection_text += "Чтобы пользоваться услугами Proxy Hunter и получать самые свежие прокси, "
            rejection_text += "необходимо быть участником нашего сообщества."
            
            bot.send_message(chat_id, rejection_text, reply_markup=sub_keyboard, parse_mode="Markdown")
            return
            
        # Б) РАЗБОР КОМАНД
        base_command = input_text.split()[0].lower()
        
        # Команда СТАРТ
        if base_command == '/start':
            welcome_text = "🦾 **ДОБРО ПОЖАЛОВАТЬ В PROXY HUNTER v14.3**\n\n"
            welcome_text += "Я — профессиональный бот для поиска прокси, оптимизированный под работу в РФ.\n\n"
            welcome_text += "🛰 /get — Сгенерировать список прокси\n"
            welcome_text += "❓ /help — Справка и техподдержка"
            bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
            
        # Команда ПОЛУЧИТЬ ПРОКСИ
        elif base_command == '/get':
            # Отправляем временное сообщение, чтобы юзер видел процесс
            loading_message = bot.send_message(chat_id, "🛰 **Поиск активных узлов...**\nПожалуйста, подождите, я проверяю пинг.")
            
            # Получаем прокси через мастер-загрузчик
            final_selection = master_proxy_fetcher(6)
            
            if final_selection:
                response_payload = "📡 **АКТУАЛЬНЫЕ MTPROTO ДЛЯ РФ:**\n\n"
                for entry in final_selection:
                    response_payload += f"{entry['visual']} **{entry['ping_val']}ms** — [ПОДКЛЮЧИТЬ]({entry['connection_url']})\n\n"
                
                # Обновляем сообщение со списком
                bot.edit_message_text(
                    text=response_payload,
                    chat_id=chat_id,
                    message_id=loading_message.message_id,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                bot.edit_message_text(
                    text="❌ **ПРОКСИ НЕ НАЙДЕНЫ**\nВ данный момент все узлы проходят проверку. Повторите попытку позже.",
                    chat_id=chat_id,
                    message_id=loading_message.message_id
                )
                
        # Команда ПОМОЩЬ
        elif base_command == '/help':
            help_payload = "🛰 **ИНФОРМАЦИЯ И КОНТАКТЫ**\n\n"
            help_payload += f"🌐 **Веб-версия:** {PROJECT_WEB_LINK}\n"
            help_payload += "🛰 **Описание:** Бот ищет только те прокси, которые имеют маскировку для обхода систем DPI.\n\n"
            help_payload += f"🛠 **Поддержка:** {SUPPORT_USER}\n"
            help_payload += f"👑 **Администратор:** @{ADMIN_NICKNAME}"
            
            bot.send_message(chat_id, help_payload, parse_mode="Markdown", disable_web_page_preview=True)

        # Команда ПОСТ ДЛЯ КАНАЛА (Только для админа)
        elif base_command == '/post':
            if msg.from_user.username == ADMIN_NICKNAME:
                preparing_notif = bot.send_message(chat_id, "⏳ Генерирую пост для канала...")
                
                post_proxies = master_proxy_fetcher(5)
                
                if post_proxies:
                    final_post = "🛰 **НОВЫЙ ПАКЕТ MTPROTO ПРОКСИ**\n\n"
                    for item in post_proxies:
                        final_post += f"{item['visual']} Пинг: **{item['ping_val']}ms**\n🔗 {item['connection_url']}\n\n"
                    
                    final_post += f"🌐 Весь список в реальном времени: {PROJECT_WEB_LINK}"
                    
                    # Отправка в основной канал
                    bot.send_message(PRIMARY_CHANNEL, final_post, parse_mode="Markdown", disable_web_page_preview=True)
                    bot.edit_message_text("✅ Пост успешно опубликован!", chat_id, preparing_notif.message_id)
                else:
                    bot.edit_message_text("❌ Ошибка при генерации поста.", chat_id, preparing_notif.message_id)
            else:
                bot.send_message(chat_id, "⛔️ У вас нет прав для выполнения данной команды.")

# ---------------------------------------------------------
# [ РАЗДЕЛ 6: ТОЧКА ВХОДА И ЗАПУСК СЕРВИСОВ ]
# ---------------------------------------------------------

def execute_bot_polling():
    """Запускает бесконечный цикл опроса Telegram API"""
    # Небольшая пауза для корректной инициализации на Render
    time.sleep(15)
    logger.info("Запуск Telegram Polling...")
    try:
        bot.polling(none_stop=True, interval=0, timeout=50)
    except Exception as fatal_error:
        logger.error(f"Критический сбой в Polling: {fatal_error}")
        time.sleep(10)
        # Рекурсивный перезапуск при сбое
        execute_bot_polling()

if __name__ == "__main__":
    # 1. Запуск потока бота
    bot_thread = Thread(target=execute_bot_polling)
    bot_thread.daemon = True
    bot_thread.start()
    
    # 2. Определение порта для Render
    web_port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Запуск веб-сервера на порту {web_port}")
    
    # 3. Запуск Flask в основном потоке
    try:
        app.run(host='0.0.0.0', port=web_port, debug=False, use_reloader=False)
    except Exception as flask_fatal:
        logger.error(f"Критический сбой Flask: {flask_fatal}")
