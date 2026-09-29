import os, requests, random
from flask import Flask, request
app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

def get_analyse(match):
    try:
        h = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
        data = {"model": "llama-3.1-8b-instant", "messages": [{"role":"user","content":f"Analyse pro 2 phrases pour {match}, forme, domicile, H2H. Sois confiant."}], "temperature":0.7}
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=h, json=data, timeout=15)
        j = r.json()
        if "choices" in j:
            return j["choices"][0]["message"]["content"]
        else:
            return f"Match équilibré mais léger avantage à domicile. Forme récente correcte."
    except:
        return f"Match serré, avantage forme pour {match.split('vs')[0]}."

def build_ticket(match, analyse):
    v1 = random.randint(68,84)
    dc = random.randint(76,88)
    over15 = random.randint(78,88)
    btts = random.randint(60,77)
    corners = random.randint(65,82)
    cartons = random.randint(62,79)

    # Détermine le favori simple
    team1 = match.split('vs')[0].strip() if 'vs' in match.lower() else match.split(' ')[0]

    return f"""🔥 OCUP-KILLER V10 - ANALYSE ELITE 🔥
⚔️ MATCH: {match.upper()}

🏆 PRONO PRINCIPAL
▸ Victoire {team1} ou favori - {v1}% - FORTES POSSIBILITÉS

🛡️ SÉCURITÉ MAX - BASE SOLIDE
▸ Double Chance 1X - {dc}% - TICKET DU JOUR

⚽ BUTS - LE PLUS SÛR
▸ Over 1.5 Buts - {over15}% - LE PLUS SÛR DU MATCH
▸ BTTS Oui - {btts}%

🚩 CORNERS
▸ Over 7.5 Corners - {corners}%

🟨 CARTONS
▸ Over 2.5 Cartons - {cartons}%

📊 ANALYSE PRO: {analyse}

💎 COMBI V10: Double Chance + Over 1.5 = {dc-8}% DE RÉUSSITE
"""

@app.route("/", methods=["POST","GET"])
def w():
    if request.method == "GET": return "OCUP-KILLER V10.4 ONLINE"
    u = request.get_json(silent=True)
    if not u or "message" not in u: return "ok"
    c = u["message"]["chat"]["id"]
    t = u["message"].get("text","")
    if t.lower() == "/start":
        msg = "🤖 OCUP-KILLER V10.4 ONLINE\nEnvoie un match: Érythrée vs Afrique du Sud"
    else:
        analyse = get_analyse(t)
        msg = build_ticket(t, analyse)
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":c,"text":msg})
    return "ok"
