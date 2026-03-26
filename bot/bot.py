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

# --- [ КОНФИГ ] ---
TOKEN = '8764406808:AAEwgPjf4K4CxJ8ZUfDy8G2XOCYCoP2a1HM'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa"
WEB_URL = "https://proxy-rhe6.onrender.com"

bot = telebot.TeleBot(TOKEN)
users = set()

# --- [ ЛОГИКА "REAL-FEEL" (ФИЛЬТР СВЕРХЗВУКОВЫХ ПРОКСИ) ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
        # ОЧЕНЬ короткий таймаут 0.4с. Если прокси не "ракета", он нам не нужен.
        sock = socket.create_connection((srv, int(prt)), timeout=0.4)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        # Берем только те, что для бота < 100мс. 
        # Это гарантирует, что у юзеров (с учетом их инета) будет в районе 150мс.
        if ms <= 100:
            return {'ms': ms, 'icon': "🚀", 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}", 'server': srv}
    except:
        pass
    return None

def get_best_proxies(limit=6):
    sources = ["https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"]
    try:
        r = requests.get(sources[0], timeout=5)
        raw_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text)
        unique = list(set(raw_list))
        random.shuffle(unique)
        
        # Проверяем сразу 150 штук за раз для максимального выбора
        with ThreadPoolExecutor(max_workers=60) as executor:
            results = list(executor.map(check_proxy, unique[:150]))
        
        valid = [r for r in results if r]
        # Сортируем от самых быстрых к менее быстрым
        return sorted(valid, key=lambda x: x['ms'])[:limit]
    except:
        return []

# --- [ ВЕБ-САЙТ ДЛЯ СТАБИЛЬНОСТИ ] ---
app = Flask('')

@app.route('/ping')
def ping(): 
    return "OK", 200 # Для cron-job.org

@app.route('/')
def home():
    proxies = get_best_proxies(8)
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Proxy Hunter Web</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: #0f172a; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 20px; }
            .container { max-width: 500px; margin: 0 auto; background: #1e293b; padding: 20px; border-radius: 20px; border: 1px solid #334155; }
            .proxy-card { background: #334155; margin: 10px 0; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
            .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 15px; border-radius: 8px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛰 PROXY HUNTER</h1>
            <p>Только прокси со скоростью ракеты 🚀</p>
            {% for p in proxies %}
            <div class="proxy-card">
                <div style="text-align:left"><b>⚡️ {{ p.ms }}ms</b> (server)</div>
                <a href="{{ p.url }}" class="btn">ВКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
            <br>
            <button onclick="location.reload()" class="btn" style="background:#f59e0b;">ОБНОВИТЬ СПИСОК</button>
        </div>
    </body>
    </html>
    """
    return render_template_string(HTML_TEMPLATE, proxies=proxies)

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    bot.send_message(m.chat.id, "🦾 **PROXY HUNTER v14.5**\n\nЯ теперь ищу только прокси с пингом до **100мс**, чтобы у тебя всё летало!\n\n🛰 /get — Поиск ракет\n❓ /help — Инфо")

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "⚡️ **Фильтрую медленные прокси...**")
    best = get_best_proxies(5)
    if best:
        res = "💎 **ЭЛИТНЫЕ MTPROTO (ПИНГ < 100ms):**\n\n"
        for p in best:
            res += f"🚀 **{p['ms']}ms** — [ПОДКЛЮЧИТЬ]({p['url']})\n\n"
        res += "⚠️ *У тебя пинг может быть чуть выше из-за провайдера, но это лучшее, что есть в сети.*"
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        bot.edit_message_text("❌ Сейчас супер-быстрых прокси не найдено. Попробуй через минуту!", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = (
        "❓ **КАК ЭТО РАБОТАЕТ?**\n\n"
        "Бот проверяет сотни прокси и оставляет только те, где задержка минимальна. Если у тебя всё равно тормозит:\n"
        "— Смени 4G на Wi-Fi (или наоборот)\n"
        "— Попробуй самый верхний прокси из списка /get\n\n"
        "💡 **ПОДДЕРЖКА:** [КЛИК СЮДА](" + SUPPORT_LINK + ")"
    )
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        best = get_best_proxies(5)
        if best:
            post_text = "🛰 **ЛЮТЕЙШАЯ ИМБА (ПИНГ < 100ms)**\n\n"
            for p in best: post_text += f"🚀 Пинг: **{p['ms']}ms**\n{p['url']}\n\n"
            post_text += f"🌐 Наш сайт: {WEB_URL}\n📢 Подпишись на {CHANNEL_ID}"
            bot.send_message(CHANNEL_ID, post_text, disable_web_page_preview=True)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **ADMIN**\nЮзеров: {len(users)}\n/post — Рассылка")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
