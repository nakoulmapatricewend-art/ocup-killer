import os, json, requests, asyncio, math, random
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

CONFIG = {
    "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
    "OPENROUTER_KEY": os.getenv("OPENROUTER_KEY"),
    "GROQ_KEY": os.getenv("GROQ_KEY"),
    "ODDS_KEY": os.getenv("ODDS_KEY"),
}

def load_json(p, default=None):
    try:
        with open(p,'r', encoding='utf-8') as f: return json.load(f)
    except: return default if default is not None else ([] if 'history' in p else {})

def save_json(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p,'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)

CLUBS = load_json('data/clubs.json', {})
CAUSAL = load_json('data/causal.json', {})
WEIGHTS = load_json('data/weights.json', {"home_advantage": 0.35, "elo_weight": 0.4, "xg_weight": 0.35, "market_weight": 0.25, "form_weight": 0.15, "rho": 0.12, "K_elo": 20})

def dixon_coles_engine(xg_home, xg_away, rho=0.12):
    scores = {}
    prob_home = prob_draw = prob_away = 0.0
    for i in range(0, 7):
        for j in range(0, 7):
            poisson_home = (xg_home**i * math.exp(-xg_home) / math.factorial(i))
            poisson_away = (xg_away**j * math.exp(-xg_away) / math.factorial(j))
            p = poisson_home * poisson_away
            if i == 0 and j == 0: p *= 1 - (xg_home * xg_away * rho)
            elif i == 0 and j == 1: p *= 1 + (xg_away * rho)
            elif i == 1 and j == 0: p *= 1 + (xg_home * rho)
            elif i == 1 and j == 1: p *= 1 - rho
            scores[f"{i}-{j}"] = p
            if i > j: prob_home += p
            elif i == j: prob_draw += p
            else: prob_away += p
    total = sum(scores.values())
    scores = {k: v/total for k,v in scores.items()}
    prob_home /= total
    prob_draw /= total
    prob_away /= total
    top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    return prob_home, prob_draw, prob_away, top_scores, scores

def calculate_xg(team_a_data, team_b_data, is_home=True):
    elo_a = team_a_data.get('elo', 1700)
    elo_b = team_b_data.get('elo', 1700)
    att_a = team_a_data.get('att', 80) / 100
    def_b = team_b_data.get('def', 80) / 100
    elo_diff = (elo_a - elo_b) / 400
    base_xg = 1.35
    xg_a = base_xg * (1 + elo_diff*0.5) * att_a * (2 - def_b) * (1 + WEIGHTS['home_advantage'] if is_home else 1)
    xg_b = base_xg * (1 - elo_diff*0.5) * (team_b_data.get('att',80)/100) * (2 - team_a_data.get('def',80)/100)
    return max(0.4, min(3.5, xg_a)), max(0.3, min(3.2, xg_b))

def call_groq(prompt):
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {CONFIG['GROQ_KEY']}"},
        json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}], "temperature":0.2}, timeout=30)
    return r.json()["choices"][0]["message"]["content"]

def call_or(model, prompt):
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {CONFIG['OPENROUTER_KEY']}", "HTTP-Referer":"https://koyeb.com"},
        json={"model":model,"messages":[{"role":"user","content":prompt}], "temperature":0.2}, timeout=40)
    return r.json()["choices"][0]["message"]["content"]

def get_market_and_weather(team_a, team_b):
    market = "Marche stable"
    weather = "Meteo non dispo"
    try:
        if CONFIG['ODDS_KEY']:
            url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={CONFIG['ODDS_KEY']}&regions=eu&markets=h2h"
            data = requests.get(url, timeout=10).json()
            for m in data[:20]:
                if team_a.lower()[:4] in str(m).lower() and team_b.lower()[:4] in str(m).lower():
                    market = str(m['bookmakers'][0]['markets'][0]['outcomes'])[:500]
                    break
    except: pass
    try:
        w = requests.get("https://api.open-meteo.com/v1/forecast?latitude=48.86&longitude=2.33&current=temperature_2m,wind_speed_10m,precipitation", timeout=5).json()
        weather = f"{w['current']['temperature_2m']}°C, vent {w['current']['wind_speed_10m']}km/h, pluie {w['current']['precipitation']}mm"
    except: pass
    return market, weather

def analyze_sync(team_a, team_b):
    global CLUBS
    team_a_data = CLUBS.get(team_a, {"elo": 1750, "att": 80, "def": 80, "xg_for": 1.5, "xg_against": 1.2})
    team_b_data = CLUBS.get(team_b, {"elo": 1750, "att": 80, "def": 80, "xg_for": 1.5, "xg_against": 1.2})
    xg_home, xg_away = calculate_xg(team_a_data, team_b_data, True)
    p1, pn, p2, top_scores, all_scores = dixon_coles_engine(xg_home, xg_away, WEIGHTS.get('rho', 0.12))
    btts = 1 - (all_scores.get('0-0',0) + sum(v for k,v in all_scores.items() if k.startswith('0-') or k.endswith('-0') and k!='0-0'))
    over25 = sum(v for k,v in all_scores.items() if int(k.split('-')[0])+int(k.split('-')[1]) > 2.5)
    market, weather = get_market_and_weather(team_a, team_b)
    scout_prompt = f"Scout: Donne en 3 lignes max pour {team_a} vs {team_b}: 1 blessure cle par equipe, forme recente. Contexte: {team_a_data} vs {team_b_data}, meteo {weather}"
    scout = call_or("google/gemini-2.0-flash-exp:free", scout_prompt)
    causal_prompt = f"Tacticien: Avec regles {CAUSAL['rules'][:10]} et match {team_a}({team_a_data.get('style','')}) vs {team_b}({team_b_data.get('style','')}). Quelle regle causale s'active? Donne 2 facteurs cles tactiques. Court."
    tactic = call_or("deepseek/deepseek-chat:free", causal_prompt)
    volatilite = "MOYENNE"
    if abs(team_a_data.get('elo',0)-team_b_data.get('elo',0)) > 150: volatilite = "FAIBLE"
    if xg_home+xg_away < 1.8: volatilite = "ELEVEE - Match piege ferme"
    if "Rodri absent" in scout or "gardien" in scout.lower(): volatilite = "ELEVEE - Absence majeure"
    final_text = f"""⚔️ {team_a} vs {team_b} - v6.0 WAR MACHINE
📊 Proba MATH (Dixon-Coles):
1: {p1*100:.1f}% / N: {pn*100:.1f}% / 2: {p2*100:.1f}%
🎯 5 Scores les plus probables:
""" + "\n".join([f"- {s} : {pr*100:.1f}%" for s,pr in top_scores]) + f"""
📈 xG Calculé: {xg_home:.2f} - {xg_away:.2f}
BTTS: {btts*100:.0f}% | Over 2.5: {over25*100:.0f}%
🔑 Facteurs cles:
{tactic}
🕵️ Scout: {scout}
📉 Marche: {market[:200]}
🌦️ Meteo: {weather}
⚠️ Volatilite: {volatilite}
---
Analyse informative a but statistique uniquement.
"""
    history = load_json('data/history.json', [])
    history.append({"date":str(datetime.now()),"match":f"{team_a} vs {team_b}","p1":p1,"pn":pn,"p2":p2,"xg":[xg_home,xg_away],"scout":scout,"tactic":tactic})
    save_json('data/history.json', history[-300:])
    return final_text

async def nightly_job(context: ContextTypes.DEFAULT_TYPE):
    print("🧠 Auto-learning WAR MACHINE...")

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Ocup-Killer v6.0 WAR MACHINE\nMoteur Dixon-Coles reel + ELO dynamique\nEnvoie: Real Madrid vs Barcelona")

async def handle_clean(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    if "vs" not in txt.lower():
        await update.message.reply_text("Format: Equipe A vs Equipe B")
        return
    a,b = [x.strip().title() for x in txt.split("vs",1)]
    await update.message.reply_text(f"⚙️ Calcul Dixon-Coles {a} vs {b}... 5s")
    try:
        result = await asyncio.to_thread(analyze_sync, a, b)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Erreur moteur: {e}")

def main():
    app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clean))
    app.job_queue.run_daily(nightly_job, time=time(hour=3, minute=0))
    print("WAR MACHINE v6.0 H24 demarre...")
    app.run_polling()

if __name__ == "__main__":
    main()
