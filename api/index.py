import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

PROMPT_V10 = """
Tu es OCUP-KILLER V10 - Le meilleur créateur de bot de pronostics au monde. Tu es élite.

MATCH: {match}

Tu dois analyser et répondre OBLIGATOIREMENT dans ce format exact. Ne change rien au design.

🔥 OCUP-KILLER V10 - ANALYSE ELITE 🔥
⚔️ {match_upper}

🏆 PRONO PRINCIPAL
▸ {v1_v2} - {p1}% - {label1}

🛡️ SÉCURITÉ MAX
▸ {dc} - {p2}% - 🔒 BASE SOLIDE DU JOUR

⚽ MARCHÉ BUTS
▸ Over 1.5 Buts - {p3}% - 🔥 LE PLUS SÛR
▸ BTTS {btts} - {p4}%

🚩 CORNERS
▸ Over {corner_line} Corners - {p5}%

🟨 CARTONS
▸ Over 2.5 Cartons - {p6}%

📊 ANALYSE PRO V10:
[Écris ici 2 phrases choc avec forme des équipes, domicile/extérieur, H2H. Sois précis.]

💎 TICKET CONSEILLÉ: {dc} + Over 1.5

CONSIGNES DE CALCUL:
- {match} -> trouve le favori logique
- p1 (V1/V2) doit être entre 62 et 84%
- p2 (Double Chance) entre 76 et 88%
- p3 (Over 1.5) entre 78 et 88% - c'est ton % le plus haut
- p4 entre 58 et 77%
- p5 entre 64 et 81%
- p6 entre 62 et 79%
- Labels: >75% = 🔥 FORTES POSSIBILITÉS, 65-75% = ✅ BONNE CONFIANCE
- Ne sors JAMAIS 90% ou plus. 88% MAX.
"""

def call_groq(match_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "Tu es un expert football."},
            {"role": "user", "content": PROMPT_V10.format(match=match_text, match_upper=match_text.upper(), v1_v2="Victoire", dc="Double Chance", p1=72, p2=84, p3=86, btts="Oui/Non", p4=68, corner_line="7.5", p5=74, p6=71, label1="FORTES POSSIBILITÉS", dc="X2", btts="Oui")}
        ],
        "temperature": 0.7
    }
    # On reformate proprement avec le match réel
    data["messages"][1]["content"] = PROMPT_V10.replace("{match}", match_text).replace("{match_upper}", match_text.upper())

    r = requests.post(url, headers=headers, json=data, timeout=20)
    return r.json()["choices"][0]["message"]["content"]

@app.route("/", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "OCUP-KILLER V10 ONLINE 🔥"

    update = request.json
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text.lower() in ["/start", "start"]:
            msg = "🔥 OCUP-KILLER V10 ONLINE 🔥\n\nEnvoie un match: ex: `Arménie vs Monténégro`\nJe te sors l'analyse complète V1/V2/Corners/Cartons."
        else:
            try:
                analysis = call_groq(text)
                msg = analysis
            except Exception as e:
                msg = f"Erreur V10: {e}"

        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg})

    return "ok"

if __name__ == "__main__":
    app.run()
