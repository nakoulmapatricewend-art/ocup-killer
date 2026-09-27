import os, requests
from flask import Flask, request
app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
@app.route("/api/index", methods=["GET","POST"])
def w():
    BOT = os.getenv("BOT_TOKEN")
    KEY = os.getenv("GROQ_API_KEY")

    if request.method == "GET":
        return f"v7 OK - BOT exists:{bool(BOT)} - GROQ exists:{bool(KEY)}", 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        msg = data.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        txt = (msg.get("text") or "").strip()
        if not chat: return "ok",200

        if not BOT:
            requests.post(f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/sendMessage", json={"chat_id":chat,"text":"ERREUR: BOT_TOKEN vide sur Vercel"})
            return "ok",200

        if txt == "/start":
            rep = "🤖 Ocup-Killer v7 ONLINE\nEnvoie un match: Real vs Barca"
        else:
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {KEY}"},
                    json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":txt}],"max_tokens":300}, timeout=10)
                rep = r.json()["choices"][0]["message"]["content"]
            except Exception as e:
                rep = f"Erreur Groq: {e} | KEY ok:{bool(KEY)}"

        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id":chat,"text":rep}, timeout=5)
    except Exception as e:
        print(f"CRASH TOTAL: {e}")
    return "ok",200
