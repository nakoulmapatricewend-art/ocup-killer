from flask import Flask, request
import os, requests, traceback

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN") or "").strip()
app = Flask(__name__)

def send(chat_id, text):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        print(f"Send error: {e}")

@app.route('/', methods=['GET','POST'])
def home():
    if request.method == 'GET':
        return "OCUP-KILLER v6.0 READY", 200
    try:
        data = request.get_json(force=True)
        if not data or 'message' not in data:
            return "ok", 200
        msg = data['message']
        chat_id = msg['chat']['id']
        text = msg.get('text','').strip()
        if not text:
            return "ok", 200
        if text == '/start':
            send(chat_id, "🤖 <b>Ocup-Killer v6.0 ONLINE</b>\n\nEnvoie: Real Madrid vs Barcelona")
            return "ok", 200
        if 'vs' in text.lower():
            send(chat_id, f"⚙️ Calcul {text}...")
            try:
                from bot import analyze_sync
                result = analyze_sync(text)
                send(chat_id, result)
            except Exception as e:
                print(traceback.format_exc())
                send(chat_id, f"❌ Erreur: {str(e)[:800]}")
            return "ok", 200
        send(chat_id, "Format: Equipe A vs Equipe B")
        return "ok", 200
    except Exception as e:
        print(traceback.format_exc())
        return "ok", 200
