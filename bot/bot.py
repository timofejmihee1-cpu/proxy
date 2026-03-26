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
TOKEN = '8764406808:AAF2jaeyaLtCYbufyxcNQ8u-jnGc33NrQOc'
ADMIN_USERNAME = "PR1SM_777" 
SUPPORT_LINK = "https://t.me/Ovekin_777_bot" 
CHANNEL_ID = "@proxy_timoxa"
WEB_URL = "https://proxy-rhe6.onrender.com"

bot = telebot.TeleBot(TOKEN)
users = set()

# --- [ ЛОГИКА ПРОКСИ ] ---
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

# --- [ ВЕБ-САЙТ С КАЗИНО ] ---
app = Flask('')

@app.route('/ping')
def ping():
    return "OK", 200 # Специально для cron-job.org, чтобы не было ошибки "вывод слишком большой"

@app.route('/')
def home():
    proxies = get_fresh_proxies(8)
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
            .footer { margin-top: 30px; font-size: 13px; color: #64748b; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛰 PROXY HUNTER</h1>
            <p style="color:#94a3b8">Выбери прокси из списка или испытай удачу:</p>
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
        </script>
    </body>
    </html>
    """
    return render_template_string(HTML_TEMPLATE, proxies=proxies, px_json=json.dumps(proxies), support=SUPPORT_LINK)

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run); t.daemon = True; t.start()

# --- [ КОМАНДЫ БОТА ] ---
@bot.message_handler(commands=['start'])
def start_cmd(m):
    users.add(m.chat.id)
    text = (
        "🦾 **PROXY HUNTER v14.3**\n\n"
        "🛰 /get — Поиск быстрых прокси\n"
        "❓ /help — Помощь и поддержка"
    )
    bot.send_message(m.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['get'])
def get_cmd(m):
    users.add(m.chat.id)
    wait_msg = bot.send_message(m.chat.id, "🛰 **Ищу лучшие варианты...**")
    valid = get_fresh_proxies(6)
    if valid:
        res = "📡 **АКТУАЛЬНЫЕ MTPROTO:**\n\n"
        for p in valid: res += f"{p['icon']} **{p['ms']}ms** — {p['url']}\n\n"
        res += (
            "⚠️ **ВНИМАНИЕ:**\n"
            "Некоторые прокси могут не работать из-за ограничений твоего **оператора** или **Wi-Fi**. "
            "Если не грузит — попробуй следующий из списка.  подпишись на https://t.me/proxy_timoxa"
            
        )
        bot.edit_message_text(res, m.chat.id, wait_msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ Прокси не найдены. Попробуй /get еще раз.", m.chat.id, wait_msg.message_id)

@bot.message_handler(commands=['help'])
def help_cmd(m):
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
        "💡 **ПОДДЕРЖКА:** [КЛИК СЮДА](" + SUPPORT_LINK + ")"
    )
    bot.send_message(m.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['post'])
def post_cmd(m):
    if m.from_user.username == ADMIN_USERNAME:
        valid = get_fresh_proxies(5)
        if valid:
            post_text = "🛰 **СВЕЖИЕ ПРОКСИ**\n\n"
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
