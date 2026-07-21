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

# ==================== KEEP-ALIVE FUNCTION ====================

def keep_alive():
    """Keep the bot alive by logging status every minute"""
    while True:
        uptime = datetime.datetime.now() - start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        print(f"💚 Bot is alive! Uptime: {hours}h {minutes}m | Messages: {message_count}")
        time.sleep(60)

# ==================== SCRAPE FUNCTION ====================

def scrape_bdgdu():
    """Scrape data from bdgdu.com using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = browser.new_page()
            
            page.goto("http://bdgdu.com/#/", timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            title = page.title()
            links = page.eval_on_selector_all('a', 'els => els.map(el => el.href)')
            
            game_data = []
            try:
                elements = page.query_selector_all('[class*="game"], [class*="result"], [class*="color"], [class*="number"]')
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

# ==================== STORE FUNCTIONS ====================

def save_history(data):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "title": data.get("title", "N/A"),
        "links_count": data.get("links_count", 0),
        "game_data_count": len(data.get("game_data", [])),
        "data": data
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

# ==================== TELEGRAM FUNCTIONS ====================

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
    payload = {"chat_id": chat_id, "action": "typing"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# ==================== COMMAND HANDLERS ====================

def handle_start():
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    return f"""🎯 <b>JA CLUB KING BOT</b> ✅

📌 <b>Commands:</b>
/ping - Check bot status
/time - Current server time
/scrape - Scrape & store data
/show - Show current data
/history - Show scrape history
/stats - Storage statistics
/help - Help menu
/about - About bot

🕐 <b>Uptime:</b> {hours}h {minutes}m
📊 <b>Messages:</b> {message_count}

💾 Data store enabled!
🤖 24/7 Running!"""

def handle_ping():
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    return f"""🏓 <b>Pong!</b>

✅ Bot is alive!
🕐 Uptime: {hours}h {minutes}m
📊 Total messages: {message_count}
💚 Status: Active"""

def handle_time():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"🕐 <b>Server Time:</b> {now}"

def handle_scrape(chat_id):
    send_message(chat_id, "⏳ Scraping in progress...")
    data = scrape_bdgdu()
    
    if data["success"]:
        return f"""✅ <b>Scraping Complete!</b>
        
📌 <b>Title:</b> {data['title']}
🔗 <b>Links Found:</b> {data['links_count']}
🎯 <b>Game Data:</b> {len(data['game_data'])} items
📝 <b>Preview:</b> {data['body_preview'][:200]}...

💾 <b>Data Stored!</b>
🕐 Time: {data['timestamp']}

📊 Type /show to see data
📈 Type /history for all scrapes"""
    else:
        return f"❌ Error: {data['error']}"

def handle_show():
    data = load_current_data()
    
    if data and data.get("success"):
        game_text = "\n".join([f"  🎯 {item}" for item in data.get('game_data', [])[:5]])
        if not game_text:
            game_text = "  No game data found"
        
        return f"""📊 <b>Current Scraped Data</b>

📌 <b>Title:</b> {data.get('title', 'N/A')}
🔗 <b>Links Found:</b> {data.get('links_count', 0)}
🎯 <b>Game Data:</b> {len(data.get('game_data', []))} items
🕐 <b>Scraped At:</b> {data.get('timestamp', 'N/A')}

<b>📋 Game Data Items:</b>
{game_text}

📝 <b>Preview:</b>
{data.get('body_preview', 'N/A')[:200]}...

💾 <b>File:</b> {DATA_FILE}"""
    else:
        return "❌ No scraped data found! Type /scrape first."

def handle_history():
    history = load_history()
    
    if not history:
        return "❌ No scrape history found! Type /scrape first."
    
    msg = f"""📚 <b>Scrape History</b> (Last 10)
    
📊 <b>Total Scrapes:</b> {len(history)}
"""
    
    for i, entry in enumerate(history[-10:], 1):
        msg += f"""
{i}. 🕐 {entry.get('timestamp', 'N/A')[:16]}
   📌 {entry.get('title', 'N/A')}
   🔗 Links: {entry.get('links_count', 0)}
   🎯 Games: {entry.get('game_data_count', 0)}"""
    
    return msg

def handle_stats():
    stats = get_stats()
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    return f"""📊 <b>Bot Statistics</b>

🤖 <b>Bot:</b> JA CLUB KING
🕐 <b>Uptime:</b> {hours}h {minutes}m
📊 <b>Messages:</b> {message_count}

<b>📁 Storage Stats:</b>
📌 <b>Total Scrapes:</b> {stats['total_scrapes']}
🕐 <b>Last Scrape:</b> {stats['last_scrape']}
📁 <b>Current Data:</b> {'✅ Yes' if stats['current_data'] else '❌ No'}

💡 Type /scrape to add more data
📊 Type /show to view data"""

def handle_help():
    return f"""📚 <b>Help Menu</b>

🔄 <b>Data Commands:</b>
/scrape - Scrape & store data
/show - Show current data
/history - Show scrape history
/stats - Show storage stats

ℹ️ <b>Info Commands:</b>
/ping - Check bot status
/time - Current server time
/start - Welcome message
/help - This menu
/about - About bot

🤖 Bot runs 24/7!
💾 Data store enabled!"""

def handle_about():
    uptime = datetime.datetime.now() - start_time
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    
    return f"""🤖 <b>About JA CLUB KING BOT</b>

📌 <b>Bot Name:</b> JA CLUB KING
🔑 <b>Version:</b> 1.0.0
🕐 <b>Uptime:</b> {hours}h {minutes}m
📊 <b>Messages:</b> {message_count}

<b>Features:</b>
✅ 24/7 Running
✅ Webhook enabled
✅ Data storage
✅ Scraping support

<b>Developer:</b> @YourUsername"""

# ==================== MAIN HANDLER ====================

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
        reply = f"📨 You said: <b>{text}</b>\n\nType /help for commands."
    
    return reply

# ==================== FLASK ROUTES ====================

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
        print(f"❌ Webhook Error: {e}")
        return jsonify({"status": "error"}), 500

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🤖 JA CLUB KING BOT is starting...")
    print(f"🔑 Token: {BOT_TOKEN[:10]}...")
    print("✅ Scrape + Store enabled!")
    print("✅ 24/7 mode enabled!")
    
    # Start keep-alive thread
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    
    app.run(host="0.0.0.0", port=8080, debug=False)
