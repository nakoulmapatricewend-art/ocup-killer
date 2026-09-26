import os, requests
from flask import Flask, request
app = Flask(__name__)
BOT = os.getenv("BOT_TOKEN")
KEY = os.getenv("GROQ_API_KEY")

def groq(q):
    if not KEY: return "❌ GROQ_API_KEY manquante"
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {KEY}"},
            json={"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":f"Prono court pour {q}"}],"max_tokens":400},
            timeout=8)
        d = r.json()
        print(d)
        if r.status_code!=200: return f"Groq:{d.get('error',{}).get('message',d)}"
        return d["choices"][0]["message"]["content"]
    except Exception as e: return f"Err:{e}"

@app.route("/", methods=["GET","POST"])
@app.route("/api/index", methods=["GET","POST"])
def w():
    if request.method=="GET": return "v6.2 OK",200
    msg = request.get_json().get("message",{})
    chat = msg.get("chat",{}).get("id")
    txt = msg.get("text","")
    if not chat: return "ok",200
    rep = "🤖 Ocup-Killer v6.2 ONLINE\nEnvoie: Real Madrid vs Barcelona" if txt=="/start" else groq(txt)
    requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id":chat,"text":rep}, timeout=5)
    return "ok",200
