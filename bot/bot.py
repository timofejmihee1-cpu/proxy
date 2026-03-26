import telebot
import requests
import re
import time
import random
import socket
from concurrent.futures import ThreadPoolExecutor
from flask import Flask
from threading import Thread

# --- [ КОНФИГ ] ---
TOKEN = '8764406808:AAEwgPjf4K4CxJ8ZUfDy8G2XOCYCoP2a1HM'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_BOT = "@Ovekin_777_bot" # Твой бот поддержки

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
users = set()

# --- [ БУДИЛЬНИК ] ---
app = Flask('')
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- [ ЛОГИКА ПРОВЕРКИ ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
        sock = socket.create_connection((srv, int(prt)), timeout=1.0)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        if ms < 150: icon = "🟢"
        elif ms < 300: icon = "🟡"
        else: icon = "🔴"
            
        return {'ms': ms, 'icon': icon, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}"}
    except: return None

# --- [ КОМАНДЫ ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    text = (
        "🦾 **PROXY HUNTER v11.0**\n\n"
        "🛰 /get — Поиск быстрых прокси\n"
        "❓ /help — Помощь и поддержка"
    )
    bot.send_message(m.chat.id, text)

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "🛰 **Ищу лучшие варианты...**")
    
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/tgproxies.txt"
    ]
    
    raw_list = []
    for url in sources:
        try:
            r = requests.get(url, timeout=5)
            raw_list.extend(re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text))
        except: continue
    
    unique = list(set(raw_list))
    random.shuffle(unique)
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_proxy, unique[:80]))
    
    valid = sorted([r for r in results if r], key=lambda x: x['ms'])[:6]
    
    if valid:
        response = "📡 **АКТУАЛЬНЫЕ MTPROTO:**\n\n"
        for i, p in enumerate(valid):
            response += f"{p['icon']} **{p['ms']}ms** — [ПОДКЛЮЧИТЬ]({p['url']})\n"
        
        response += (
            "\n⚠️ **ВНИМАНИЕ:**\n"
            "Некоторые прокси могут не работать из-за ограничений оператора или Wi-Fi. Если не грузит — попробуйте следующий."
        )
        bot.edit_message_text(response, m.chat.id, wait_msg.message_id, disable_web_page_preview=True)
    else:
        bot.edit_message_text("❌ Нет доступных прокси. Попробуй /get еще раз.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = (
        "❓ **ИНФОРМАЦИЯ**\n\n"
        "🟢 — Пинг отличный\n"
        "🟡 — Пинг средний\n"
        "🔴 — Медленно\n\n"
        "🛑 **ПРОБЛЕМЫ?**\n"
        "Если прокси не подключается, попробуйте сменить тип интернета (Wi-Fi/4G) или выбрать другой вариант в списке.\n\n"
        f"💡 **ЕСТЬ ИДЕЯ?**\n"
        f"Мы всегда рады вашим предложениям по улучшению бота! Нашли баг или хотите предложить новую функцию? Пишите в нашу поддержку: {SUPPORT_BOT}"
    )
    bot.send_message(m.chat.id, help_text)

# --- [ АДМИНКА ] ---
@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **ADMIN**\nЮзеров: {len(users)}\nРассылка: `/send текст`")

@bot.message_handler(commands=['send'])
def send_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        text = m.text.replace('/send', '').strip()
        if text:
            for u_id in users:
                try: bot.send_message(u_id, f"📢 **ОБЪЯВЛЕНИЕ:**\n\n{text}")
                except: continue
            bot.send_message(m.chat.id, "✅ Рассылка завершена.")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
