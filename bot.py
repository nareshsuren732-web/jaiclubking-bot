from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 🔑 YOUR BOT TOKEN
BOT_TOKEN = "8781051659:AAFOMdE0DhkfhD55PezQ35ccoBNI4viOpaU"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"✅ Sent: {r.status_code}")
        return r
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"📨 Received: {data}")
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            reply = f"✅ Bot is working! You said: {text}"
            send_message(chat_id, reply)
            
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "no message"})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    print("🤖 Bot is starting...")
    app.run(host="0.0.0.0", port=8080, debug=False) 
