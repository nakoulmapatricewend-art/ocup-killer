import os, requests
from flask import Flask, request
app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
@app.route("/api/index", methods=["GET","POST"])
def w():
    BOT = os.getenv("BOT_TOKEN")
    KEY = os.getenv("GROQ_API_KEY")

    if request.method == "GET":
        return f"v7 PRO OK - BOT:{bool(BOT)} - GROQ:{bool(KEY)}", 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        msg = data.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        txt = (msg.get("text") or "").strip()
        if not chat: return "ok",200
        if not BOT: return "ok",200

        if txt == "/start":
            rep = "🤖 Ocup-Killer v7 ONLINE\nEnvoie un match: ex: Burkina vs RCA"
        else:
            try:
                prompt_system = """Tu es Ocup-Killer V7, expert pari sportif Burkinabé.
Règles OBLIGATOIRES:
- Réponds TOUJOURS en français
- JAMAIS de ** ou de tableau markdown |
- Utilise exactement ce format avec emojis:

🤖 OCUP-KILLER V7
⚽ MATCH: [Equipe A vs Equipe B]
📊 PRONO:
✅ Victoire: [nom]
✅ BTTS: Oui/Non
✅ Over 2.5: Oui/Non
✅ Score exact: [ex: 2-0]

Mini-analyse:
2 phrases max, style Etalons, direct.
"""

                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {"role": "system", "content": prompt_system},
                            {"role": "user", "content": f"Match à analyser: {txt}"}
                        ],
                        "max_tokens": 350,
                        "temperature": 0.6
                    }, timeout=15)

                j = r.json()
                if "choices" in j:
                    rep = j["choices"][0]["message"]["content"]
                else:
                    rep = f"Groq dit: {j}"
            except Exception as e:
                rep = f"Erreur: {e}"

        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id": chat, "text": rep}, timeout=10)
    except Exception as e:
        print(f"CRASH: {e}")
    return "ok",200
