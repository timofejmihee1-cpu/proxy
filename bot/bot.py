import telebot
import requests
import re
import time
import random
import socket
from concurrent.futures import ThreadPoolExecutor
from telebot import types
from flask import Flask
from threading import Thread

# --- [ КОНФИГ ] ---
TOKEN = '8764406808:AAEwgPjf4K4CxJ8ZUfDy8G2XOCYCoP2a1HM'
ADMIN_USERNAME = "PR1SM_777" 

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
users = set()

# --- [ БУДИЛЬНИК ] ---
app = Flask('')
@app.route('/')
def home(): return "OK"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- [ МЕНЮ ] ---
def get_main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text="🛰 Найти быстрые прокси", callback_data="get_proxy"),
        types.InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    )
    return kb

# --- [ ЛОГИКА ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
        sock = socket.create_connection((srv, int(prt)), timeout=1.0)
        sock.close()
        ms = int((time.time() - start) * 1000)
        return {'ms': ms, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}"}
    except: return None

# --- [ КОМАНДЫ ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    bot.send_message(m.chat.id, "🦾 **PROXY HUNTER v8.0**\nНажми кнопку ниже, чтобы получить список прокси.", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['admin'])
def admin_secret(m):
    if m.from_user.username == ADMIN_USERNAME:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="📢 Рассылка", callback_data="adm_broadcast"))
        kb.add(types.InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats"))
        bot.send_message(m.chat.id, "👑 **Секретная панель админа**", reply_markup=kb)

# --- [ КНОПКИ ] ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    users.add(call.message.chat.id) # Авто-добавление в базу
    
    if call.data == "get_proxy":
        bot.answer_callback_query(call.id, "Начинаю поиск...")
        bot.edit_message_text("🛰 **Сканирую источники...**", call.message.chat.id, call.message.message_id)
        
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
            results = list(executor.map(check_proxy, unique[:100]))
        
        valid = sorted([r for r in results if r], key=lambda x: x['ms'])[:7]
        
        if valid:
            kb = types.InlineKeyboardMarkup(row_width=1)
            for i, p in enumerate(valid):
                kb.add(types.InlineKeyboardButton(text=f"🟢 #{i+1} — {p['ms']}ms", url=p['url']))
            kb.add(types.InlineKeyboardButton(text="🔄 Найти еще", callback_data="get_proxy"))
            bot.edit_message_text("✅ **Самые быстрые прокси:**", call.message.chat.id, call.message.message_id, reply_markup=kb)
        else:
            bot.edit_message_text("❌ Нет живых прокси. Попробуй позже.", call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard())

    elif call.data == "help":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Просто нажми 'Найти прокси'. Бот выдаст ссылки, при нажатии на которые прокси сами добавятся в твой Telegram.")

    elif call.data == "adm_stats":
        bot.answer_callback_query(call.id, f"Пользователей: {len(users)}", show_alert=True)

    elif call.data == "adm_broadcast":
        msg = bot.send_message(call.message.chat.id, "Введите текст для рассылки:")
        bot.register_next_step_handler(msg, perform_broadcast)

def perform_broadcast(m):
    count = 0
    for u_id in users:
        try:
            bot.send_message(u_id, f"📢 **Объявление:**\n\n{m.text}")
            count += 1
        except: continue
    bot.send_message(m.chat.id, f"✅ Рассылка завершена. Доставлено: {count}")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
