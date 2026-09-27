import os, requests
from flask import Flask, request
app = Flask(__name__)

# --- REGLAGES FACILES ---
SEUIL_ALERTE = 75 # % pour déclencher "FORTES POSSIBILITES"
MODE_LIVE = True
FOOT_KEY = os.getenv("FOOTBALL_API_KEY") # tu l'ajouteras demain

@app.route("/", methods=["GET","POST"])
@app.route("/api/index", methods=["GET","POST"])
def w():
    BOT = os.getenv("BOT_TOKEN")
    GROQ = os.getenv("GROQ_API_KEY")
    if request.method == "GET":
        return f"v8 OK BOT:{bool(BOT)} GROQ:{bool(GROQ)} LIVE:{bool(FOOT_KEY)}", 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        msg = data.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        txt = (msg.get("text") or "").strip()
        if not chat or not BOT: return "ok",200

        if txt == "/start":
            rep = "🤖 OCUP-KILLER V8 ONLINE\n\nEnvoie: Burkina vs RCA\nEnvoie: Burkina vs RCA live\n\nTout est réglable en haut de index.py"
        else:
            is_live = "live" in txt.lower() and MODE_LIVE

            # 1. Récupère live si demandé
            live_info = ""
            if is_live and FOOT_KEY:
                try:
                    r = requests.get("https://v3.football.api-sports.io/fixtures?live=all",
                        headers={"x-apisports-key": FOOT_KEY}, timeout=10).json()
                    live_info = f"Donnees live API: {str(r['response'][:2])}"
                except:
                    live_info = "API Live indisponible"

            # 2. Analyse Groq avec proba
            prompt = f"""
Tu es Ocup-Killer V8. Analyse: {txt}. {live_info}
REGLES:
- Francais uniquement
- JAMAIS de ** ou tableau
- Donne TOUJOURS un % de probabilité pour chaque prono
- Si un prono > {SEUIL_ALERTE}%, commence par: 🚨 MATCH A FORTES POSSIBILITES 🚨

FORMAT EXACT:
🤖 OCUP-KILLER V8
⚽ MATCH: X vs Y
{ "📡 LIVE: [score et minute si dispo]" if is_live else "" }

📊 PRONO & PROBA:
✅ Victoire: [equipe] - [XX]%
✅ BTTS: Oui/Non - [XX]%
✅ Over 2.5: Oui/Non - [XX]%
✅ Score exact: [score] - [XX]%

🧠 Analyse: 2 phrases max.
"""

            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-oss-20b",
                    "messages": [{"role":"user","content":prompt}],
                    "max_tokens": 400,
                    "temperature": 0.5
                }, timeout=20)
            j = r.json()
            rep = j["choices"][0]["message"]["content"] if "choices" in j else f"Erreur Groq: {j}"

        requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage",
            json={"chat_id": chat, "text": rep}, timeout=10)
    except Exception as e:
        print(f"CRASH: {e}")
    return "ok",200
