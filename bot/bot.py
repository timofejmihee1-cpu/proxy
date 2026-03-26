import telebot
import requests
import re
import time
import random
import socket
import json
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template_string, request
from threading import Thread
from telebot import types

# --- [ КОНФИГ ] ---
TOKEN = '8764406808:AAEwgPjf4K4CxJ8ZUfDy8G2XOCYCoP2a1HM'
ADMIN_USERNAME = "PR1SM_777" 
ADMIN_PASS = "TIMOXA_BOSS_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa"
WEB_URL = "https://proxy-rhe6.onrender.com"

bot = telebot.TeleBot(TOKEN)
users = set()
logs = [] 

def add_log(action):
    t = time.strftime("%H:%M:%S")
    logs.append(f"[{t}] {action}")
    if len(logs) > 30: logs.pop(0)

# --- [ ЛОГИКА ПРОВЕРКИ ПРОКСИ ] ---
def check_proxy(p_data):
    srv, prt, sec = p_data
    try:
        start = time.time()
        sock = socket.create_connection((srv, int(prt)), timeout=0.8)
        sock.close()
        ms = int((time.time() - start) * 1000)
        
        if ms < 150: icon = "🟢"
        elif ms < 300: icon = "🟡"
        else: icon = "🔴"
            
        return {'ms': ms, 'icon': icon, 'url': f"tg://proxy?server={srv}&port={prt}&secret={sec}", 'server': srv}
    except: return None

def get_fresh_proxies(limit=8):
    sources = ["https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"]
    raw_list = []
    try:
        r = requests.get(sources[0], timeout=5)
        raw_list = re.findall(r'server=([^&]+)&port=(\d+)&secret=([^&\s]+)', r.text)
    except: return []
    
    unique = list(set(raw_list))
    random.shuffle(unique)
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(check_proxy, unique[:60]))
    
    return sorted([r for r in results if r], key=lambda x: x['ms'])[:limit]

# --- [ ВЕБ-САЙТ С КАЗИНО И АДМИНКОЙ ] ---
app = Flask('')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Proxy Hunter Web + Casino</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: -apple-system, sans-serif; text-align: center; padding: 20px; margin: 0; }
        .container { max-width: 500px; margin: 20px auto; background: #1e293b; padding: 25px; border-radius: 20px; box-shadow: 0 15px 30px rgba(0,0,0,0.4); border: 1px solid #334155; }
        h1 { color: #38bdf8; font-size: 28px; }
        .proxy-card { background: #334155; margin-bottom: 12px; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; }
        .btn { background: #38bdf8; color: #0f172a; text-decoration: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; border: none; }
        
        .casino-box { margin-top: 30px; padding: 20px; border: 2px dashed #f59e0b; border-radius: 15px; background: #1e293b; }
        #wheel { width: 80px; height: 80px; border: 4px solid #f59e0b; border-radius: 50%; margin: 15px auto; display: flex; align-items: center; justify-content: center; font-size: 40px; transition: transform 0.5s; }
        .spinning { animation: spin 0.3s linear infinite; }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        
        #result-link { display: none; margin-top: 15px; padding: 12px; background: #22c55e; border-radius: 8px; color: white; text-decoration: none; font-weight: bold; }
        .btn:disabled { background: #475569; cursor: not-allowed; }
        
        .admin-link { margin-top: 40px; font-size: 11px; color: #475569; cursor: pointer; text-decoration: underline; opacity: 0.5; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 100; }
        .admin-panel { background: #1e293b; width: 90%; max-width: 400px; margin: 40px auto; padding: 20px; border-radius: 15px; border: 2px solid #38bdf8; }
        .log-box { text-align: left; font-size: 12px; background: #0f172a; padding: 10px; height: 180px; overflow-y: auto; color: #22c55e; border-radius: 5px; font-family: monospace; }
        .footer { margin-top: 30px; font-size: 13px; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰 PROXY HUNTER</h1>
        <p style="color:#94a3b8">Выбери прокси из списка или испытатай удачу:</p>
        
        <div id="proxy-list">
            {% for p in proxies %}
            <div class="proxy-card">
                <div style="text-align:left">
                    <span style="font-weight:bold">{{ p.icon }} {{ p.ms }}ms</span><br>
                    <small style="color:#94a3b8">{{ p.server[:20] }}</small>
                </div>
                <a href="{{ p.url }}" class="btn">ВКЛЮЧИТЬ</a>
            </div>
            {% endfor %}
        </div>

        <div class="casino-box">
            <h3 style="color:#f59e0b; margin-top:0;">🎰 ПРОКСИ-КАЗИНО</h3>
            <div id="wheel">🎲</div>
            <button onclick="spinWheel()" id="spin-button" class="btn" style="background: #f59e0b;">КРУТИТЬ КОЛЕСО</button>
            <a href="#" id="result-link"></a>
        </div>

        <div class="footer">
            Создано Тимофеем | <a href="{{ support }}" style="color:#38bdf8; text-decoration:none;">Поддержка</a>
        </div>
        
        <div class="admin-link" onclick="document.getElementById('adminModal').style.display='block'">Панель управления</div>
    </div>

    <div id="adminModal" class="modal">
        <div class="admin-panel">
            <h2 id="adm-title">ВХОД В АДМИНКУ</h2>
            <div id="login-form">
                <input type="password" id="pass" placeholder="Пароль..." style="padding:10px; border-radius:5px; border:none; width:80%; background:#334155; color:white;"><br><br>
                <button class="btn" onclick="checkPass()">ВОЙТИ</button>
                <button class="btn" style="background:#ef4444" onclick="document.getElementById('adminModal').style.display='none'">ОТМЕНА</button>
            </div>
            <div id="adm-content" style="display:none;">
                <p>Всего пользователей: <b>{{ user_count }}</b></p>
                <h4 style="margin-bottom:5px;">ЛОГИ ДЕЙСТВИЙ:</h4>
                <div class="log-box">{% for l in logs %}{{ l }}<br>{% endfor %}</div><br>
                <button class="btn" style="background:#f59e0b" onclick="location.reload()">ОБНОВИТЬ ДАННЫЕ</button>
                <button class="btn" onclick="document.getElementById('adminModal').style.display='none'">ЗАКРЫТЬ</button>
            </div>
        </div>
    </div>

    <script>
        const proxies = {{ px_json | safe }};
        function spinWheel() {
            if (proxies.length === 0) return alert("Обнови страницу!");
            const wheel = document.getElementById('wheel');
            const btn = document.getElementById('spin-button');
            const resLink = document.getElementById('result-link');
            btn.disabled = true; resLink.style.display = 'none'; wheel.classList.add('spinning');
            setTimeout(() => {
                wheel.classList.remove('spinning');
                const p = proxies[Math.floor(Math.random() * proxies.length)];
                wheel.innerHTML = p.icon; resLink.href = p.url; resLink.style.display = 'block';
                resLink.innerHTML = "✅ ВЫПАЛ " + p.ms + "ms - ЖМИ!"; btn.disabled = false;
            }, 2000);
        }
        function checkPass() {
            const p = document.getElementById('pass').value;
            if(p === "{{ admin_pass }}") {
                document.getElementById('login-form').style.display = 'none';
                document.getElementById('adm-content').style.display = 'block';
                document.getElementById('adm-title').innerText = "АДМИН-ПАНЕЛЬ";
            } else { alert("НЕВЕРНЫЙ ПАРОЛЬ!"); }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
    return render_template_string(HTML_TEMPLATE, proxies=proxies, px_json=json.dumps(proxies), user_count=len(users), logs=logs, admin_pass=ADMIN_PASS, support=SUPPORT_LINK)

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    add_log(f"Юзер {m.from_user.username or m.chat.id} зашел в бота")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_web = types.InlineKeyboardButton("🌐 ОТКРЫТЬ НАШ САЙТ", url=WEB_URL)
    btn_get = types.InlineKeyboardButton("🛰 ПОЛУЧИТЬ ПРОКСИ", callback_data="get_prx")
    btn_help = types.InlineKeyboardButton("❓ ПОМОЩЬ", callback_data="help_prx")
    markup.add(btn_web, btn_get, btn_help)
    
    text = (
        "🦾 **PROXY HUNTER v16.1**\n\n"
        "Рады видеть тебя! Выбирай действие ниже:"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "get_prx":
        get_cmd(call.message)
    elif call.data == "help_prx":
        help_cmd(call.message)

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    add_log(f"Запрос прокси от {m.chat.id}")
    wait_msg = bot.send_message(m.chat.id, "🛰 **Ищу лучшие варианты...**")
    valid = get_fresh_proxies(6)
    if valid:
        res = "📡 **АКТУАЛЬНЫЕ MTPROTO:**\n\n"
        for p in valid: res += f"{p['icon']} **{p['ms']}ms** — {p['url']}\n\n"
        res += (
            "⚠️ **ВНИМАНИЕ:**\n"
            "Некоторые прокси могут не работать из-за ограничений твоего **оператора** или **Wi-Fi**. "
            "Если не грузит — попробуй следующий из списка или наш сайт."
        )
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Прокси не найдены. Попробуй /get еще раз.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['help'])
def help_cmd(m):
    add_log(f"Юзер открыл помощь")
    help_text = (
        "❓ **ИНФОРМАЦИЯ**\n\n"
        "🟢 — Пинг отличный\n"
        "🟡 — Пинг средний\n"
        "🔴 — Медленно\n\n"
        "🛑 **ПРОБЛЕМЫ?**\n"
        "Провайдеры интернета часто блокируют порты. Если прокси не подключается:\n"
        "— Попробуй сменить Wi-Fi на мобильный интернет (или наоборот)\n"
        "— Выбери другой вариант в списке\n"
        "— Используй наш сайт с Казино: " + WEB_URL + "\n\n"
        "💡 **ЕСТЬ ИДЕЯ?**\n"
        "Мы всегда рады вашим предложениям! Пишите в нашу поддержку: [КЛИК СЮДА](" + SUPPORT_LINK + ")"
    )
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        add_log("Админ сделал рассылку в канал")
        valid = get_fresh_proxies(5)
        if valid:
            post_text = "🛰 **СВЕЖИЕ ПРОКСИ + КАЗИНО**\n\n"
            for p in valid: post_text += f"{p['icon']} Пинг: **{p['ms']}ms**\n{p['url']}\n\n"
            post_text += f"🌐 Наш сайт: {WEB_URL}\n📢 Подпишись на {CHANNEL_ID}"
            bot.send_message(CHANNEL_ID, post_text, disable_web_page_preview=True)

@bot.message_handler(commands=['admin'])
def admin_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        bot.send_message(m.chat.id, f"👑 **ADMIN**\nЮзеров: {len(users)}\n/post — Пост в канал")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
