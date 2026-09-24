from flask import Flask, request
import os, sys, asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Prend TELEGRAM_TOKEN ou TOKEN (pour éviter l'erreur)
TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN") or os.getenv("BOT_TOKEN") or "").strip()

if not TOKEN:
    raise ValueError("TOKEN vide ! Va dans Vercel > Settings > Environment Variables")

application = Application.builder().token(TOKEN).build()

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Ocup-Killer v6.0 WAR MACHINE Vercel ON\nEnvoie: Real Madrid vs Barcelona")

async def handle_clean(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    if "vs" not in txt.lower():
        await update.message.reply_text("Format: Equipe A vs Equipe B")
        return
    a,b = [x.strip().title() for x in txt.split("vs",1)]
    await update.message.reply_text(f"⚙️ Calcul {a} vs {b}... 5s")
    try:
        result = await asyncio.to_thread(bot.analyze_sync, a, b)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Erreur: {e}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clean))

flask_app = Flask(__name__)

@flask_app.route('/', methods=['GET', 'POST'])
@flask_app.route('/api/index.py', methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        async def process():
            await application.initialize()
            await application.process_update(Update.de_json(request.get_json(force=True), application.bot))
        asyncio.run(process())
    return "WAR MACHINE ONLINE", 200

app = flask_app
