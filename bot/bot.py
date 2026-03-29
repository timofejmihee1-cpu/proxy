# =================================================================
# ПРОЕКТ: PROXY HUNTER v14.3 - FINAL ULTIMATE EDITION
# СТАТУС: ИСПРАВЛЕНЫ ВСЕ ОШИБКИ (HELP, GET, FILTERS)
# =================================================================

import telebot
import requests
import re
import time
import random
import socket
import json
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template_string
from threading import Thread

# ---------------------------------------------------------
# [ РАЗДЕЛ 1: ПАРАМЕТРЫ И КОНФИГУРАЦИЯ ]
# ---------------------------------------------------------

TOKEN = '8764406808:AAESVgV_PKemfwMaN5bdwiH3rgtXeYyMYOs'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_TAG = "@Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa" 
LOG_CHANNEL_ID = "@logi_proxy" 
CHANNEL_LINK = "https://t.me/proxy_timoxa"
WEB_LINK = "https://proxy-rhe6.onrender.com"

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Бот с увеличенным количеством рабочих потоков
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=100)

# ---------------------------------------------------------
# [ РАЗДЕЛ 2: СЛУЖЕБНЫЕ ПРОВЕРКИ ]
# ---------------------------------------------------------

def check_member(user_id):
    """Проверяет подписку на канал"""
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Subscription Check Error: {e}")
        return True # В случае сбоя — пропускаем

def send_to_logs(message):
    """Отправляет лог действий в канал @logi_proxy"""
    try:
        u = message.from_user
        log_data = (
            f"🛰 **ДЕЙСТВИЕ ПОЛЬЗОВАТЕЛЯ**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Имя: {u.first_name}\n"
            f"🔗 Юзер: @{u.username if u.username else 'нет'}\n"
            f"🆔 ID: `{u.id}`\n"
            f"💬 Текст: {message.text if message.text else '[Медиа]'}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(LOG_CHANNEL_ID, log_data, parse_mode="Markdown")
    except:
        pass

# ---------------------------------------------------------
# [ РАЗДЕЛ 3: МОЩНЫЙ АГРЕГАТОР И ФИЛЬТР ПРОКСИ ]
# ---------------------------------------------------------

def check_node_status(proxy_info, strict_mode=False):
    """
    Проверяет прокси на пинг и доступность порта.
    """
    host, port, secret = proxy_info
    try:
        t_start = time.time()
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(1.5) # Хороший таймаут для РФ
        
        # Проверка коннекта
        result = conn.connect_ex((host, int(port)))
        conn.close()
        
        if result == 0:
            ping = int((time.time() - t_start) * 1000)
            
            # Логика фильтрации
            is_stealth = secret.startswith(('ee', 'dd'))
            
            # Фильтр: отсекаем совсем мертвые или фейковые (0-50мс)
            if ping < 60 or ping > 1200:
                return None
            
            # В строгом режиме (для канала) отдаем приоритет TLS
            if strict_mode and not is_stealth and ping < 150:
                return None

            # Подбор иконки
            if ping < 300: emoji = "🟢"
            elif ping < 600: emoji = "🟡"
            else: emoji = "🔴"
            
            return {
                'latency': ping,
                'icon': emoji,
                'link': f"tg://proxy?server={host}&port={port}&secret={secret}",
                'ip': host
            }
    except:
        return None

def fetch_master_list(limit=8):
    """
    Собирает прокси из ГИГАНТСКОГО списка источников.
    """
    urls = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/Hookzof/free-proxies/main/mtproto.txt",
        "https://raw.githubusercontent.com/Proxy-List/Proxy-List/master/mtproto.txt",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2RayCollector/main/proxy/mtproto",
        "https://raw.githubusercontent.com/Moghadam7/MTProtoProxy/main/MTProtoProxy.txt",
        "https://raw.githubusercontent.com/Paimon-Genshin/MTProto-Collector/main/proxy.txt",
        "https://raw.githubusercontent.com/biplobsd/MTProto-Proxy-List/master/proxy.txt",
        "https://raw.githubusercontent.com/MuhammedKalkan/Telegram-MTProto-List/master/proxies.txt",
        "https://raw.githubusercontent.com/Ellion-Design/MTProto-Proxy-List/main/proxies.txt",
        "https://raw.githubusercontent.com/Zizigum/MTProto-Proxy-List/main/proxy.txt"
    ]
    
    all_raw = []
    
    # Сбор данных из всех репозиториев
    for u in urls:
        try:
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                matches = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text)
                all_raw.extend(matches)
        except:
            continue
            
    # Удаляем дубликаты и перемешиваем
    unique_pool = list(set(all_raw))
    random.shuffle(unique_pool)
    
    verified = []
    
    # Используем 120 потоков для мгновенного чека
    with ThreadPoolExecutor(max_workers=120) as executor:
        # Проверяем первые 400 штук из базы
        tasks = [executor.submit(check_node_status, p, True) for p in unique_pool[:400]]
        for t in as_completed(tasks):
            res = t.result()
            if res:
                verified.append(res)
                
    # Сортировка по пингу
    return sorted(verified, key=lambda x: x['latency'])[:limit]

# ---------------------------------------------------------
# [ РАЗДЕЛ 4: ВЕБ-САЙТ ДЛЯ RENDER ]
# ---------------------------------------------------------

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PROXY HUNTER | ULTIMATE</title>
    <style>
        body { background: #0b0f19; color: #e5e7eb; font-family: 'Inter', sans-serif; text-align: center; margin: 0; padding: 15px; }
        .container { max-width: 500px; margin: auto; background: #111827; padding: 25px; border-radius: 25px; border: 1px solid #1e40af; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
        h1 { color: #3b82f6; font-size: 28px; text-transform: uppercase; margin-bottom: 5px; }
        .proxy-card { background: #1f2937; margin: 12px 0; padding: 18px; border-radius: 15px; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; transition: 0.2s; }
        .proxy-card:hover { border-color: #3b82f6; background: #374151; }
        .btn { background: #3b82f6; color: white; text-decoration: none; padding: 10px 20px; border-radius: 10px; font-weight: bold; font-size: 14px; }
        .refresh { background: #d97706; color: white; border: none; padding: 16px; width: 100%; border-radius: 15px; cursor: pointer; font-weight: bold; margin-top: 15px; font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰 PROXY HUNTER</h1>
        <p style="color:#6b7280; font-size:12px;">OPTIMIZED FOR BYPASSING 🇷🇺</p>
        {% for p in proxies %}
        <div class="proxy-card">
            <div style="text-align:left">
                <span style="font-size:18px;">{{p.icon}} {{p.latency}}ms</span><br>
                <small style="color:#9ca3af;">{{p.ip[:22]}}</small>
            </div>
            <a href="{{p.link}}" class="btn">ВКЛЮЧИТЬ</a>
        </div>
        {% endfor %}
        <button onclick="location.reload()" class="refresh">ОБНОВИТЬ СПИСОК</button>
    </div>
</body>
</html>
"""

@app.route('/')
def main_page():
    data = fetch_master_list(15)
    return render_template_string(INDEX_HTML, proxies=data)

# ---------------------------------------------------------
# [ РАЗДЕЛ 5: ОБРАБОТКА КОМАНД (ИСПРАВЛЕНО) ]
# ---------------------------------------------------------

@bot.message_handler(func=lambda message: True)
def main_router(message):
    """
    Единый роутер команд. Все проверки внутри.
    """
    # Логируем всё
    send_to_logs(message)
    
    # Если это не текст или не команда — выходим
    if not message.text or not message.text.startswith('/'):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.split()[0].lower()

    # СРАЗУ ПРОВЕРЯЕМ ПОДПИСКУ
    if not check_member(user_id):
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("🚀 Подписаться на канал", url=CHANNEL_LINK))
        bot.send_message(chat_id, "⚠️ **ДОСТУП ЗАБЛОКИРОВАН**\n\nЧтобы пользоваться ботом, подпишись на наш канал!", reply_markup=kb, parse_mode="Markdown")
        return

    # --- БЛОК КОМАНД (РАБОТАЕТ ВСЕГДА) ---

    if text == '/start':
        start_msg = (
            "🦾 **ДОБРО ПОЖАЛОВАТЬ В PROXY HUNTER v14.3**\n\n"
            "Я нахожу лучшие прокси для работы Telegram в РФ.\n\n"
            "🛰 /get — Список прокси\n"
            "❓ /help — Помощь и контакты"
        )
        bot.send_message(chat_id, start_msg, parse_mode="Markdown")

    elif text == '/help':
        # Теперь эта кнопка работает моментально!
        help_msg = (
            "🛰 **ИНФОРМАЦИЯ И ПОДДЕРЖКА**\n\n"
            f"🌐 **Наш сайт:** {WEB_LINK}\n"
            "🛰 **Команда:** `/get` — выдает список из 6 проверенных прокси.\n\n"
            f"🛠 **Тех. поддержка:** {SUPPORT_TAG}\n"
            f"👑 **Администратор:** @{ADMIN_USERNAME}"
        )
        bot.send_message(chat_id, help_msg, parse_mode="Markdown", disable_web_page_preview=True)

    elif text == '/get':
        loading = bot.send_message(chat_id, "🛰 **Запуск сканирования...**\nОпрашиваю узлы на пинг.")
        
        proxies = fetch_master_list(6)
        
        if proxies:
            res_txt = "📡 **АКТУАЛЬНЫЕ MTPROTO (DPI Bypass):**\n\n"
            for p in proxies:
                res_txt += f"{p['icon']} **{p['latency']}ms** — [ПОДКЛЮЧИТЬ]({p['link']})\n\n"
            
            bot.edit_message_text(res_txt, chat_id, loading.message_id, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            bot.edit_message_text("❌ **ОШИБКА**\nПрокси не найдены. Попробуйте снова через минуту.", chat_id, loading.message_id)

    elif text == '/admin':
        if message.from_user.username == ADMIN_USERNAME:
            bot.send_message(chat_id, "👑 **АДМИН-ПАНЕЛЬ**\n\nИспользуй `/post` для отправки списка в канал.")
        else:
            bot.send_message(chat_id, "❌ У вас нет прав.")

    elif text == '/post':
        if message.from_user.username == ADMIN_USERNAME:
            m_wait = bot.send_message(chat_id, "⏳ Генерирую пост...")
            items = fetch_master_list(5)
            if items:
                post = "🛰 **СВЕЖИЙ ПАКЕТ ПРОКСИ ДЛЯ РФ**\n\n"
                for i in items:
                    post += f"{i['icon']} Пинг: **{i['latency']}ms**\n🔗 {i['url']}\n\n"
                post += f"🌐 Весь список: {WEB_LINK}"
                
                bot.send_message(CHANNEL_ID, post, parse_mode="Markdown", disable_web_page_preview=True)
                bot.edit_message_text("✅ Опубликовано в канале!", chat_id, m_wait.message_id)
            else:
                bot.edit_message_text("❌ Ошибка генерации.", chat_id, m_wait.message_id)

# ---------------------------------------------------------
# [ РАЗДЕЛ 6: ЗАПУСК ПРИЛОЖЕНИЯ ]
# ---------------------------------------------------------

def start_bot():
    time.sleep(15) # Ожидание для Render
    logger.info(">>> Бот запущен!")
    bot.polling(none_stop=True, interval=0, timeout=60)

if __name__ == "__main__":
    # Поток для Telegram
    Thread(target=start_bot, daemon=True).start()
    
    # Запуск Flask на основном потоке
    render_port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=render_port)
