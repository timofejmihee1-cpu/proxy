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

# --- [ БУДИЛЬНИК ДЛЯ RENDER ] ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- [ КЛАВИАТУРЫ ] ---
def main_menu(username):
    kb = types.InlineKeyboardMarkup(row_width=1)
    btn_get = types.InlineKeyboardButton(text="🛰 Найти быстрые прокси", callback_data="get_proxy")
    btn_help = types.InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    kb.add(btn_get, btn_help)
    
    # Если это ты, добавляем кнопку админки
    if username == ADMIN_USERNAME:
        btn_admin = types.InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin_menu")
        kb.add(btn_admin)
    return kb

# --- [ ЛОГИКА ФИЛЬТРАЦИИ ] ---
def powerful_filter(srv, prt, sec):
    try:
        start = time.time()
        sock = socket.create_connection((srv, int(prt)), timeout=0.8) # Ускорил таймаут
        sock.close()
        ms = int((time.time() - start) * 1000)
        return {'p': ms, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}"}
    except:
        return None

# --- [ ОБРАБОТЧИКИ ] ---
@bot.message_handler(commands=['start'])
def st(m):
    bot.send_message(
        m.chat.id, 
        f"🦾 **PROXY HUNTER v7.0**\nПривет, {m.from_user.first_name}! Готов к поиску?", 
        reply_markup=main_menu(m.from_user.username)
    )

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "get_proxy":
        bot.edit_message_text("🛰 **Сканирую источники...**", call.message.chat.id, call.message.message_id)
        
        raw = []
        sources = [
            "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt", 
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/tgproxies.txt",
            "https://raw.githubusercontent.com/Jetkai/proxy-list/main/online-proxies/txt/proxies-mtproto.txt"
        ]
        
        for url in sources:
            try:
                r = requests.get(url, timeout=5)
                raw.extend(re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text))
            except: continue
        
        unique = list(set(raw))
        random.shuffle(unique)
        
        # Увеличил до 40 потоков для скорости
        with ThreadPoolExecutor(max_workers=40) as ex:
            res = list(ex.map(lambda p: powerful_filter(*p), unique[:120]))
        
        valid = sorted([r for r in res if r], key=lambda x: x['p'])[:8]
        
        if not valid:
            bot.send_message(call.message.chat.id, "❌ Прокси не найдены, попробуй позже.")
            return

        kb = types.InlineKeyboardMarkup()
        for i, p in enumerate(valid):
            kb.add(types.InlineKeyboardButton(text=f"🟢 #{i+1} — {p['p']}ms", url=p['url']))
        kb.add(types.InlineKeyboardButton(text="🔄 Найти еще", callback_data="get_proxy"))
        kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu"))

        bot.edit_message_text("✅ **Самые быстрые MTProto:**", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "admin_menu":
        if call.from_user.username == ADMIN_USERNAME:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text="📊 Статус сервера", callback_data="server_status"))
            kb.add(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu"))
            bot.edit_message_text("👑 **Панель управления PR1SM**", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data == "server_status":
        bot.answer_callback_query(call.id, "Сервер: Render Cloud\nСтатус: Online 24/7", show_alert=True)

    elif call.data == "help":
        bot.edit_message_text("Бот ищет рабочие MTProto прокси. Нажми кнопку 'Найти', выбери самый быстрый (с меньшим ms) и нажми на него.", 
                              call.message.chat.id, call.message.message_id, 
                              reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Ок", callback_data="back_to_menu")))

    elif call.data == "back_to_menu":
        bot.edit_message_text(f"🦾 **PROXY HUNTER v7.0**", call.message.chat.id, call.message.message_id, reply_markup=main_menu(call.from_user.username))

# --- [ ЗАПУСК ] ---
if __name__ == "__main__":
    keep_alive()
    print("🚀 Бот v7.0 запущен!")
    bot.polling(none_stop=True)
