import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

def call_groq(match_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Tu es OCUP-KILLER V10, expert football élite.

MATCH: {match_text}

Réponds OBLIGATOIREMENT dans ce format:

🔥 OCUP-KILLER V10 - ANALYSE ELITE 🔥
⚔️ {match_text.upper()}

🏆 PRONO PRINCIPAL
▸ Victoire [Equipe] - 62 à 84% - FORTES POSSIBILITÉS

🛡️ SÉCURITÉ MAX
▸ Double Chance 1X ou X2 ou 12 - 76 à 88% - BASE SOLIDE

⚽ BUTS
▸ Over 1.5 Buts - 78 à 88% - LE PLUS SÛR
▸ BTTS Oui ou Non - 58 à 77%

🚩 CORNERS
▸ Over 7.5 Corners - 64 à 81%

🟨 CARTONS
▸ Over 2.5 Cartons - 62 à 79%

📊 ANALYSE PRO: 2 phrases avec forme, domicile, H2H
💎 TICKET: Double Chance + Over 1.5

RÈGLES: p1 max 84%, p2 max 88%, p3 max 88%. Jamais 90%+.
"""

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    r = requests.post(url, headers=headers, json=data, timeout=20)
    res = r.json()
    return res["choices"][0]["message"]["content"]

@app.route("/", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "OCUP-KILLER V10 ONLINE"

    update = request.get_json(silent=True)
    if not update:
        return "ok"

    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text.lower() in ["/start", "start"]:
            msg = "🔥 V10 ONLINE 🔥\nEnvoie un match: Armenie vs Montenegro"
        else:
            try:
                msg = call_groq(text)
            except Exception as e:
                msg = f"Erreur: {str(e)[:200]}"

        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg})

    return "ok"
