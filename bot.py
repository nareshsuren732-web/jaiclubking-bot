from flask import Flask, request, jsonify
import requests
import time
import datetime
import json
import os
import threading

app = Flask(__name__)

# 🔑 YOUR BOT TOKEN
BOT_TOKEN = "8781051659:AAFOMdE0DhkfhD55PezQ35ccoBNI4viOpaU"

# 📁 Data files
DATA_FILE = "scraped_data.json"
HISTORY_FILE = "scrape_history.json"

# 📊 Stats
message_count = 0
start_time = datetime.datetime.now()

# ==================== KEEP-ALIVE ====================

def keep_alive():
    while True:
        uptime = datetime.datetime.now() - start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        print(f"💚 Bot alive! Uptime: {hours}h {minutes}m | Messages: {message_count}")
        time.sleep(60)

# ==================== SCRAPE ====================

def scrape_bdgdu():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page()
            page.goto("http://bdgdu.com/#/", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            title = page.title()
            links = page.eval_on_selector_all('a', 'els => els.map(el => el.href)')
            game_data = []
            try:
                elements = page.query_selector_all('[class*="game"], [class*="result"]')
                for el in elements[:20]:
                    text = el.inner_text()
                    if text.strip():
                        game_data.append(text)
            except:
                pass
            body_text = page.inner_text('body')
            browser.close()
            data = {
                "success": True,
                "title": title,
                "links_count": len(links),
                "links": links[:20],
                "game_data": game_data[:20],
                "body_preview": body_text[:500],
                "timestamp": datetime.datetime.now().isoformat()
            }
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)
            save_history(data)
            return data
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== STORE ====================

def save_history(data):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "title": data.get("title", "N/A"),
        "links_count": data.get("links_count", 0),
        "game_data_count": len(data.get("game_data", []))
    })
    if len(history) > 50:
        history = history[-50:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def load_current_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return None

def get_stats():
    history = load_history()
    current = load_current_data()
    return {
        "total_scrapes": len(history),
        "last_scrape": history[-1]["timestamp"] if history else "Never",
        "current_data": current is not None
    }

# ==================== TELEGRAM ====================

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"✅ Sent: {r.status_code}")
        return r
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def send_typing(chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except:
        pass

# ==================== COMMANDS ====================

def handle_start():
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"""🎯 <b>JA CLUB KING BOT</b> ✅

📌 <b>Commands:</b>
/ping - Check bot
/time - Current time
/scrape - Scrape & store
/show - Show data
/history - Show history
/stats - Storage stats
/help - Help menu
/about - About bot

🕐 Uptime: {hours}h {minutes}m
📊 Messages: {message_count}
💾 Data store enabled!
🤖 24/7 Running!"""

def handle_ping():
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"""🏓 Pong!

✅ Bot alive!
🕐 Uptime: {hours}h {minutes}m
📊 Messages: {message_count}"""

def handle_time():
    return f"🕐 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def handle_scrape(chat_id):
    send_message(chat_id, "⏳ Scraping...")
    data = scrape_bdgdu()
    if data["success"]:
        return f"""✅ Scraping Complete!

📌 Title: {data['title']}
🔗 Links: {data['links_count']}
🎯 Game Data: {len(data['game_data'])} items
💾 Data Stored!
🕐 {data['timestamp']}"""
    return f"❌ Error: {data['error']}"

def handle_show():
    data = load_current_data()
    if data and data.get("success"):
        game_text = "\n".join([f"  🎯 {item}" for item in data.get('game_data', [])[:5]])
        return f"""📊 Current Data

📌 Title: {data.get('title', 'N/A')}
🔗 Links: {data.get('links_count', 0)}
🎯 Game Data: {len(data.get('game_data', []))} items
🕐 Scraped: {data.get('timestamp', 'N/A')}

📋 Game Data:
{game_text if game_text else '  No game data'}"""
    return "❌ No data! Type /scrape first."

def handle_history():
    history = load_history()
    if not history:
        return "❌ No history! Type /scrape first."
    msg = f"📚 Scrape History (Last 10)\n📊 Total: {len(history)}\n"
    for i, entry in enumerate(history[-10:], 1):
        msg += f"\n{i}. 🕐 {entry.get('timestamp', 'N/A')[:16]}\n   📌 {entry.get('title', 'N/A')}\n   🔗 {entry.get('links_count', 0)} links"
    return msg

def handle_stats():
    stats = get_stats()
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"""📊 Bot Statistics

🤖 Bot: JA CLUB KING
🕐 Uptime: {hours}h {minutes}m
📊 Messages: {message_count}

📁 Storage:
📌 Total Scrapes: {stats['total_scrapes']}
🕐 Last Scrape: {stats['last_scrape']}
📁 Current Data: {'✅ Yes' if stats['current_data'] else '❌ No'}"""

def handle_help():
    return """📚 Help Menu

/scrape - Scrape & store
/show - Show data
/history - Show history
/stats - Storage stats
/ping - Check bot
/time - Current time
/start - Welcome
/about - About bot
/help - This menu

💾 Data store enabled!
🤖 24/7 Running!"""

def handle_about():
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"""🤖 About JA CLUB KING BOT

📌 Name: JA CLUB KING
🔑 Version: 1.0.0
🕐 Uptime: {hours}h {minutes}m
📊 Messages: {message_count}

Features:
✅ 24/7 Running
✅ Webhook enabled
✅ Data storage
✅ Scraping support"""

# ==================== PROCESS ====================

def process_message(chat_id, text):
    global message_count
    message_count += 1
    send_typing(chat_id)
    time.sleep(0.5)
    
    if text == "/start":
        reply = handle_start()
    elif text == "/ping":
        reply = handle_ping()
    elif text == "/time":
        reply = handle_time()
    elif text == "/scrape":
        reply = handle_scrape(chat_id)
    elif text == "/show":
        reply = handle_show()
    elif text == "/history":
        reply = handle_history()
    elif text == "/stats":
        reply = handle_stats()
    elif text == "/help":
        reply = handle_help()
    elif text == "/about":
        reply = handle_about()
    else:
        reply = f"📨 You said: {text}\n\nType /help"
    return reply

# ==================== FLASK ====================

@app.route('/')
def home():
    return "🤖 JA CLUB KING BOT is running 24/7! 💾"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"📨 Received: {data}")
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            reply = process_message(chat_id, text)
            send_message(chat_id, reply)
            return jsonify({"status": "ok"})
        return jsonify({"status": "no message"})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error"}), 500

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🤖 JA CLUB KING BOT is starting...")
    print("✅ Scrape + Store enabled!")
    print("✅ 24/7 mode enabled!")
    
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    
    app.run(host="0.0.0.0", port=8080, debug=False)
