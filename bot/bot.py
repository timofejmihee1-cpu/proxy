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
        return {'ms': ms, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}"}
    except: return None

# --- [ КОМАНДЫ ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    text = (
        "🦾 **PROXY HUNTER v9.0**\n\n"
        "Доступные команды:\n"
        "🛰 /get — Найти быстрые прокси\n"
        "❓ /help — Как это работает"
    )
    bot.send_message(m.chat.id, text)

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "🛰 **Сканирую источники...**")
    
    sources = [
        "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
        "https://raw.githubusercontent.com/hookzof/socks5_list/master/tgproxies.txt",
        "https://raw.githubusercontent.com/Jetkai/proxy-list/main/online-proxies/txt/proxies-mtproto.txt"
    ]
    
    raw_list = []
    for url in sources:
        try:
            r = requests.get(url, timeout=5)
            raw_list.extend(re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text))
        except: continue
    
    unique = list(set(raw_list))
    random.shuffle(unique)
    
    # Сканируем первые 100 штук в 30 потоков
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_proxy, unique[:100]))
    
    valid = sorted([r for r in results if r], key=lambda x: x['ms'])[:7]
    
    if valid:
        response = "✅ **Топ быстрых MTProto:**\n\n"
        for i, p in enumerate(valid):
            response += f"{i+1}️⃣ **{p['ms']}ms**\n🔗 [ПОДКЛЮЧИТЬ]({p['url']})\n\n"
        response += "Чтобы обновить список, нажми /get еще раз."
        bot.edit_message_text(response, m.chat.id, wait_msg.message_id, disable_web_page_preview=True)
    else:
        bot.edit_message_text("❌ Живых прокси не найдено. Попробуй через минуту.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    bot.send_message(m.chat.id, "Всё просто: пишешь /get, выбираешь прокси с самым маленьким **ms** и жмешь на ссылку. Telegram предложит сохранить настройки.")

# --- [ СКРЫТАЯ АДМИНКА ] ---
@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, 
            f"👑 **ADMIN PANEL**\n\n"
            f"📊 Юзеров: {len(users)}\n"
            f"📢 Рассылка: `/send Твой текст`"
        )

@bot.message_handler(commands=['send'])
def send_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        text_to_send = m.text.replace('/send', '').strip()
        if not text_to_send:
            bot.send_message(m.chat.id, "Ошибка: введи текст после команды.")
            return
        
        count = 0
        for u_id in users:
            try:
                bot.send_message(u_id, f"📢 **ОБЪЯВЛЕНИЕ:**\n\n{text_to_send}")
                count += 1
            except: continue
        bot.send_message(m.chat.id, f"✅ Разослано {count} пользователям.")

if __name__ == "__main__":
    keep_alive()
    print("🚀 Бот на командах запущен!")
    bot.polling(none_stop=True)
