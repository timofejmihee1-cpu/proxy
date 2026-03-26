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
# Твой новый токен, который ты скинул
TOKEN = '8764406808:AAF2jaeyaLtCYbufyxcNQ8u-jnGc33NrQOc'
ADMIN_USERNAME = "PR1SM_777" 
CHANNEL_ID = "@proxy_timoxa"

bot = telebot.TeleBot(TOKEN)
users = set()

# --- [ ЛОГИКА ПРОВЕРКИ ПРОКСИ ] ---
def check_proxy(p_data):
    # Формируем прямую системную ссылку tg://
    if len(p_data) == 3:
        srv, prt, sec = p_data
        url = f"tg://proxy?server={srv}&port={prt}&secret={sec}"
    else:
        srv, prt = p_data
        url = f"tg://proxy?server={srv}&port={prt}&secret=ee00000000000000000000000000000000676f6f676c652e636f6d"

    try:
        start = time.time()
        # Проверка соединения (таймаут 0.8 сек для скорости)
        sock = socket.create_connection((srv, int(prt)), timeout=0.8)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        # Цветные индикаторы пинга
        if ms < 150: icon = "🟢"
        elif ms < 300: icon = "🟡"
        else: icon = "🔴"
            
        return {'ms': ms, 'icon': icon, 'url': url, 'server': srv}
    except: return None

def get_fresh_proxies(limit=6):
    # Список источников (доноров)
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
    
    # Регулярки для поиска MTProto и обычных IP:PORT
    mtp_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', all_raw)
    socks_list = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', all_raw)
    
    combined = list(set(mtp_list + socks_list))
    random.shuffle(combined)
    
    # Проверка в 35 потоков для быстрого ответа
    with ThreadPoolExecutor(max_workers=35) as executor:
        results = list(executor.map(check_proxy, combined[:70]))
    
    # Сортировка по пингу (от быстрых к медленным)
    valid = sorted([r for r in results if r], key=lambda x: x['ms'])
    return valid[:limit]

# --- [ ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖКИ РАБОТЫ (RENDER + ТЕЛЕФОН) ] ---
app = Flask('')

@app.route('/ping')
def ping():
    return "ALIVE", 200

@app.route('/')
def home():
    return "<h1>Бот Тимохи работает!</h1><p>Используй ссылку /ping для автообновления.</p>", 200

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- [ КОМАНДЫ ТЕЛЕГРАМ-БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    bot.send_message(m.chat.id, "🛰 **PROXY HUNTER v14.7**\n\n/get — Получить быстрые прокси\n/admin — Статистика (только для админа)")

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "📡 **Ищу самые быстрые серверы...**")
    
    proxies = get_fresh_proxies(6)
    
    if proxies:
        res_text = "✅ **ГОТОВО! НАЖМИ НА ССЫЛКУ:**\n\n"
        for p in proxies:
            res_text += f"{p['icon']} Пинг: **{p['ms']}ms**\n"
            res_text += f"{p['url']}\n\n" # Ссылка без кавычек и лишних знаков
        
        bot.edit_message_text(res_text, m.chat.id, wait_msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Прокси не найдены. Попробуй еще раз через 15 секунд.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **АДМИН-ПАНЕЛЬ**\n\nВсего пользователей: {len(users)}\n/post — Рассылка прокси в канал")
    else:
        bot.send_message(m.chat.id, "🛑 У тебя нет прав админа.")

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        valid = get_fresh_proxies(5)
        if valid:
            post_text = "🛰 **СВЕЖИЕ ПРОКСИ ДЛЯ КАНАЛА**\n\n"
            for p in valid:
                post_text += f"{p['icon']} Пинг: **{p['ms']}ms**\n{p['url']}\n\n"
            bot.send_message(CHANNEL_ID, post_text)
            bot.send_message(m.chat.id, "✅ Пост отправлен в канал!")

# --- [ ЗАПУСК ] ---
if __name__ == "__main__":
    # Запускаем сайт в фоновом потоке
    Thread(target=run_web).start()
    # Запускаем бота
    print(">>> Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
