import telebot
import requests
import re
import time
import random
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from telebot import types
from flask import Flask
from threading import Thread

# --- [ КОНФИГ ] ---
TOKEN = '8764406808:AAEwgPjf4K4CxJ8ZUfDy8G2XOCYCoP2a1HM'
ADMIN_USERNAME = "PR1SM_777" 

bot = telebot.TeleBot(TOKEN)
MY_ID = None

# --- [ БУДИЛЬНИК ДЛЯ RENDER ] ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [ ЛОГИКА ФИЛЬТРАЦИИ ] ---
def powerful_filter(srv, prt, sec):
    try:
        start = time.time()
        sock = socket.create_connection((srv, int(prt)), timeout=1.0)
        sock.close()
        ms = int((time.time() - start) * 1000)
        return {'p': ms, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}"}
    except:
        return None

# --- [ ОБРАБОТЧИКИ ] ---
@bot.message_handler(commands=['start'])
def st(m):
    global MY_ID
    if m.from_user.username == ADMIN_USERNAME:
        MY_ID = m.chat.id
        bot.send_message(m.chat.id, "👑 **PR1SM ONLINE (RENDER)**")
    else:
        bot.send_message(m.chat.id, "🦾 **PROXY HUNTER v6.1**\nЖми /get")

@bot.message_handler(commands=['get'])
def gt(m):
    s = bot.send_message(m.chat.id, "🛰 **СКАНЕР...**")
    raw = []
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt", 
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/tgproxies.txt"
    ]
    for url in sources:
        try:
            r = requests.get(url, timeout=5)
            raw.extend(re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text))
        except: continue
    
    unique = list(set(raw))
    random.shuffle(unique)
    with ThreadPoolExecutor(max_workers=20) as ex:
        res = list(ex.map(lambda p: powerful_filter(*p), unique[:100]))
    
    valid = sorted([r for r in res if r], key=lambda x: x['p'])[:8]
    
    kb = types.InlineKeyboardMarkup()
    for i, p in enumerate(valid):
        kb.add(types.InlineKeyboardButton(text=f"🟢 #{i+1} — {p['p']}ms", url=p['url']))
    
    bot.delete_message(m.chat.id, s.message_id)
    bot.send_message(m.chat.id, "✅ **РЕЗУЛЬТАТЫ:**", reply_markup=kb)

# --- [ ЗАПУСК ] ---
if __name__ == "__main__":
    keep_alive() # Запуск веб-сервера
    print("🚀 Бот запущен на Render!")
    bot.polling(none_stop=True)
