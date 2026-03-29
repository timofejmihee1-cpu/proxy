# =================================================================
# ПРОЕКТ: PROXY HUNTER v14.3 - ULTIMATE EDITION (MAX)
# ОСОБЕННОСТИ: 10+ источников, Исправленный Help, Фильтр для РФ
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
# [ РАЗДЕЛ 1: КОНФИГУРАЦИЯ СИСТЕМЫ ]
# ---------------------------------------------------------

TOKEN = '8764406808:AAESVgV_PKemfwMaN5bdwiH3rgtXeYyMYOs'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "@Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa" 
LOG_CHANNEL_ID = "@logi_proxy" 
CHANNEL_URL = "https://t.me/proxy_timoxa"
WEB_URL = "https://proxy-rhe6.onrender.com"

# Логирование для Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота с поддержкой 60 потоков для скорости
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=60)

# ---------------------------------------------------------
# [ РАЗДЕЛ 2: ПРОВЕРКА ПОДПИСКИ И ЛОГИ ]
# ---------------------------------------------------------

def check_subscription(user_id):
    """Проверка, подписан ли юзер на основной канал"""
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка подписки: {e}")
        return True # Пускаем, если API тупит

def send_action_log(message):
    """Отправка подробного лога в @logi_proxy"""
    try:
        u = message.from_user
        name = u.first_name if u.first_name else "Скрыто"
        user_tag = f"@{u.username}" if u.username else "Нет"
        msg_text = message.text if message.text else "[Действие]"
        
        log_msg = (
            f"🛰 **ЛОГ СОБЫТИЯ**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Юзер: {name} ({user_tag})\n"
            f"🆔 ID: `{u.id}`\n"
            f"💬 Текст: {msg_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(LOG_CHANNEL_ID, log_msg, parse_mode="Markdown")
    except:
        pass

# ---------------------------------------------------------
# [ РАЗДЕЛ 3: ГИБКИЙ ЧЕКЕР И ГИГАНТСКАЯ БАЗА ]
# ---------------------------------------------------------

def validate_node(p_tuple, mode='strict'):
    """
    Проверка прокси. 
    'strict' - идеальные для РФ (ee/dd секреты + пинг 90-700)
    'normal' - просто рабочие (любые секреты + пинг до 1000)
    """
    srv, prt, sec = p_tuple
    try:
        start_t = time.time()
        test_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_s.settimeout(1.5) # Даем время на ответ
        
        status = test_s.connect_ex((srv, int(prt)))
        test_s.close()
        
        if status == 0:
            latency = int((time.time() - start_t) * 1000)
            
            # Фильтрация для России (DPI Bypass)
            is_stealth = sec.startswith(('ee', 'dd'))
            
            if mode == 'strict':
                # В строгом режиме ищем только те, что не забанит провайдер
                if latency < 90 or latency > 750: return None
                if not is_stealth and latency < 200: return None
            else:
                # В обычном режиме берем почти всё живое
                if latency < 50 or latency > 1100: return None

            icon = "🟢" if latency < 350 else "🟡" if latency < 600 else "🔴"
            
            return {
                'ms': latency,
                'icon': icon,
                'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}",
                'ip': srv
            }
    except:
        return None

def get_ultimate_proxies(count=8):
    """Собирает прокси из расширенного списка источников (10+ листов)"""
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/Hookzof/free-proxies/main/mtproto.txt",
        "https://raw.githubusercontent.com/Proxy-List/Proxy-List/master/mtproto.txt",
        "https://raw.githubusercontent.com/yebekhe/TelegramV2RayCollector/main/proxy/mtproto",
        "https://raw.githubusercontent.com/Moghadam7/MTProtoProxy/main/MTProtoProxy.txt",
        "https://raw.githubusercontent.com/Paimon-Genshin/MTProto-Collector/main/proxy.txt",
        "https://raw.githubusercontent.com/biplobsd/MTProto-Proxy-List/master/proxy.txt",
        "https://raw.githubusercontent.com/iam-py-test/my-proxy-list/main/mtproto.txt"
    ]
    
    raw_found = []
    
    # Сбор данных
    for url in sources:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                raw_found.extend(re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text))
        except:
            continue
            
    unique_pool = list(set(raw_found))
    random.shuffle(unique_pool)
    
    final_list = []
    
    # Шаг 1: Ищем идеальные (Строгий режим)
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(validate_node, p, 'strict') for p in unique_pool[:350]]
        for f in as_completed(futures):
            res = f.result()
            if res: final_list.append(res)
            
    # Шаг 2: Если идеальных мало, добираем обычными
    if len(final_list) < 5:
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(validate_node, p, 'normal') for p in unique_pool[:200]]
            for f in as_completed(futures):
                res = f.result()
                if res and res not in final_list: final_list.append(res)
                
    return sorted(final_list, key=lambda x: x['ms'])[:count]

# ---------------------------------------------------------
# [ РАЗДЕЛ 4: ВЕБ-САЙТ (FLASK) ]
# ---------------------------------------------------------

app = Flask(__name__)

WEB_TPL = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>PROXY HUNTER | WEB</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; text-align: center; margin: 0; padding: 20px; }
        .box { max-width: 550px; margin: auto; background: #1e293b; padding: 35px; border-radius: 30px; border: 1px solid #38bdf8; box-shadow: 0 0 30px rgba(56,189,248,0.2); }
        h1 { color: #38bdf8; letter-spacing: 2px; }
        .item { background: rgba(51, 65, 85, 0.8); margin: 12px 0; padding: 20px; border-radius: 18px; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; }
        .item:hover { border-color: #38bdf8; transform: scale(1.02); transition: 0.3s; }
        .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 12px 20px; border-radius: 12px; font-weight: bold; }
        .refresh { background: #f59e0b; color: white; border: none; padding: 18px; width: 100%; border-radius: 18px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🛰 PROXY HUNTER</h1>
        <p style="color:#94a3b8; font-size:12px;">ОБНОВЛЯЕТСЯ В РЕАЛЬНОМ ВРЕМЕНИ 🇷🇺</p>
        {% for p in proxies %}
        <div class="item">
            <div style="text-align:left"><span style="font-size:20px;">{{p.icon}} {{p.ms}}ms</span><br><small style="color:#64748b;">{{p.ip[:25]}}</small></div>
            <a href="{{p.url}}" class="btn">ВКЛЮЧИТЬ</a>
        </div>
        {% endfor %}
        <button onclick="location.reload()" class="refresh">ОБНОВИТЬ СПИСОК</button>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    p_list = get_ultimate_proxies(12)
    return render_template_string(WEB_TPL, proxies=p_list)

# ---------------------------------------------------------
# [ РАЗДЕЛ 5: ОБРАБОТКА КОМАНД БОТА ]
# ---------------------------------------------------------

@bot.message_handler(func=lambda m: True)
def router(m):
    send_action_log(m)
    
    if not m.text or not m.text.startswith('/'):
        return

    uid = m.from_user.id
    cid = m.chat.id
    
    # ПРОВЕРКА ПОДПИСКИ
    if not check_subscription(uid):
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(telebot.types.InlineKeyboardButton("🚀 Подписаться на канал", url=CHANNEL_URL))
        bot.send_message(cid, "⚠️ **ДОСТУП ОГРАНИЧЕН**\n\nДля получения прокси подпишитесь на наш канал!", reply_markup=kb, parse_mode="Markdown")
        return

    cmd = m.text.split()[0].lower()

    # ИСПРАВЛЕННЫЙ БЛОК КОМАНД
    if cmd == '/start':
        bot.send_message(cid, "🦾 **PROXY HUNTER v14.3**\n\n🛰 /get — Список прокси\n❓ /help — Помощь", parse_mode="Markdown")

    elif cmd == '/get':
        wait = bot.send_message(cid, "🛰 **Ищу лучшие прокси для РФ...**")
        data = get_ultimate_proxies(6)
        
        if data:
            txt = "📡 **АКТУАЛЬНЫЕ MTPROTO (DPI Bypass):**\n\n"
            for p in data:
                txt += f"{p['icon']} **{p['ms']}ms** — [ПОДКЛЮЧИТЬ]({p['url']})\n\n"
            bot.edit_message_text(txt, cid, wait.message_id, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            bot.edit_message_text("❌ **ОШИБКА**\nПрокси не найдены. Попробуйте снова через минуту.", cid, wait.message_id)

    elif cmd == '/help':
        help_txt = (
            "🛰 **ИНФОРМАЦИЯ И ПОМОЩЬ**\n\n"
            f"🌐 **Веб-сайт:** {WEB_URL}\n"
            "🛰 **Команда:** `/get` выдает прокси с защитой от блокировок.\n\n"
            f"🛠 **Поддержка:** {SUPPORT_LINK}\n"
            f"👑 **Админ:** @{ADMIN_USERNAME}"
        )
        bot.send_message(cid, help_txt, parse_mode="Markdown", disable_web_page_preview=True)

    elif cmd == '/post' and m.from_user.username == ADMIN_USERNAME:
        wait_p = bot.send_message(cid, "⏳ Генерирую пост...")
        items = get_ultimate_proxies(5)
        if items:
            p_msg = "🛰 **СВЕЖИЙ ПАКЕТ ПРОКСИ ДЛЯ РФ**\n\n"
            for i in items:
                p_msg += f"{i['icon']} Пинг: **{i['ms']}ms**\n🔗 {i['url']}\n\n"
            p_msg += f"🌐 Весь список: {WEB_URL}"
            bot.send_message(CHANNEL_ID, p_msg, parse_mode="Markdown", disable_web_page_preview=True)
            bot.edit_message_text("✅ Опубликовано в канале!", cid, wait_p.message_id)

# ---------------------------------------------------------
# [ РАЗДЕЛ 6: ЗАПУСК ]
# ---------------------------------------------------------

def run_polling():
    time.sleep(15)
    logger.info("Bot Polling Started...")
    bot.polling(none_stop=True, interval=0, timeout=60)

if __name__ == "__main__":
    # Запуск бота
    t = Thread(target=run_polling)
    t.daemon = True
    t.start()
    
    # Запуск сайта
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
