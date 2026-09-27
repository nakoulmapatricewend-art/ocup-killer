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
        if not BOT: return "ok",200

        if txt == "/start":
            rep = "🤖 Ocup-Killer v7 ONLINE\nEnvoie un match: Burkina vs RCA"
        else:
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {"role": "system", "content": "Tu es Ocup-Killer v7, expert pari sportif. Donne prono court 1X2, BTTS, Over 2.5 et score."},
                            {"role": "user", "content": f"Analyse: {txt}"}
                        ],
                        "max_tokens": 400,
                        "temperature": 0.7
                    }, timeout=15)
                j = r.json()
                if "choices" in j:
                    rep = j["choices"][0]["message"]["content"]
                else:
                    rep = f"Groq dit: {j}"
                    print(f"FULL GROQ ERROR: {j}")
            except Exception as e:
                rep = f"Erreur Groq: {e}"
                print(f"EXCEPTION: {e}")

        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id": chat, "text": rep}, timeout=10)
    except Exception as e:
        print(f"CRASH: {e}")
    return "ok",200
