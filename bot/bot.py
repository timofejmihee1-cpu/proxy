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

# --- [ ПОЛНЫЙ КОНФИГ ] ---
TOKEN = '8764406808:AAF2jaeyaLtCYbufyxcNQ8u-jnGc33NrQOc'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa"

bot = telebot.TeleBot(TOKEN)
users = set()

# --- [ ЛОГИКА ПРОКСИ (БЕЗ ИЗМЕНЕНИЙ) ] ---
def check_proxy(p_data):
    if len(p_data) == 3:
        srv, prt, sec = p_data
        url = f"tg://proxy?server={srv}&port={prt}&secret={sec}"
    else:
        srv, prt = p_data
        url = f"tg://proxy?server={srv}&port={prt}&secret=ee00000000000000000000000000000000676f6f676c652e636f6d"
    try:
        start = time.time()
        sock = socket.create_connection((srv, int(prt)), timeout=0.8)
        sock.close()
        ms = int((time.time() - start) * 1000)
        icon = "🟢" if ms < 150 else "🟡" if ms < 300 else "🔴"
        return {'ms': ms, 'icon': icon, 'url': url}
    except: return None

def get_fresh_proxies(limit=6):
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
    mtp_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', all_raw)
    socks_list = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', all_raw)
    combined = list(set(mtp_list + socks_list))
    random.shuffle(combined)
    with ThreadPoolExecutor(max_workers=35) as executor:
        results = list(executor.map(check_proxy, combined[:70]))
    return sorted([r for r in results if r], key=lambda x: x['ms'])[:limit]

# --- [ ВЕБ-СЕРВЕР (ДЛЯ ТЕЛЕФОНА) ] ---
app = Flask('')
@app.route('/ping')
def ping(): return "ALIVE", 200
@app.route('/')
def home(): return "<h1>Proxy Hunter Online</h1>", 200
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- [ ВСЕ КОМАНДЫ БОТА (ВОЗВРАЩЕНО ВСЁ) ] ---

@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    bot.send_message(m.chat.id, "🦾 **PROXY HUNTER v14.8**\n\n/get — Список прокси\n/casino — Испытать удачу\n/help — Помощь и саппорт")

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = (
        "❓ **КАК ПОЛЬЗОВАТЬСЯ?**\n\n"
        "1. Нажми /get\n"
        "2. Выбери прокси с зеленым кружком (🟢)\n"
        "3. Нажми на ссылку и подтверди в Telegram.\n\n"
        f"🆘 **Связь с админом:** [КЛИК]({SUPPORT_LINK})"
    )
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['casino'])
def casino_cmd(m):
    msg = bot.send_message(m.chat.id, "🎰 **Крутим рулетку...**")
    time.sleep(1)
    proxies = get_fresh_proxies(10)
    if proxies:
        p = random.choice(proxies)
        res = f"🎰 **ТВОЙ ВЫИГРЫШ:**\n\n{p['icon']} Пинг: **{p['ms']}ms**\n{p['url']}"
        bot.edit_message_text(res, m.chat.id, msg.message_id)
    else:
        bot.edit_message_text("❌ Казино закрыто, попробуй позже.", m.chat.id, msg.message_id)

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait = bot.send_message(m.chat.id, "📡 **Ищу серверы...**")
    valid = get_fresh_proxies(6)
    if valid:
        res = "📡 **АКТУАЛЬНЫЕ ПРОКСИ:**\n\n"
        for p in valid:
            res += f"{p['icon']} Пинг: **{p['ms']}ms**\n{p['url']}\n\n"
        bot.edit_message_text(res, m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("❌ Ничего не нашел, жми еще раз.", m.chat.id, wait.message_id)

# СЕКРЕТНАЯ АДМИНКА (не видна в меню)
@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **АДМИН-ПАНЕЛЬ**\n\nЮзеров: {len(users)}\n\n/post — Рассылка в канал\n/users — Список ID (в логах)")
    else:
        # Для обычных юзеров админка «не существует»
        pass 

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        valid = get_fresh_proxies(5)
        if valid:
            text = "🛰 **НОВАЯ ПАРТИЯ ПРОКСИ**\n\n"
            for p in valid: text += f"{p['icon']} **{p['ms']}ms**\n{p['url']}\n\n"
            bot.send_message(CHANNEL_ID, text)

# --- [ ЗАПУСК ] ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.polling(none_stop=True)
