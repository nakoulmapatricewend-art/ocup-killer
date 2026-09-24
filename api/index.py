from flask import Flask, request
import os

TOKEN = (os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN") or "").strip()

# --- Flask (c'est ça que Vercel doit lancer) ---
flask_app = Flask(__name__)
app = flask_app  # Vercel cherche obligatoirement 'app'

@flask_app.route('/', methods=['GET', 'POST'])
@flask_app.route('/api/index', methods=['GET', 'POST'])
def webhook():
    if request.method == "POST":
        try:
            import asyncio
            from telegram import Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            import bot as bot_logic

            # On crée l'app Telegram avec un autre nom pour ne pas confondre Vercel
            tg_app = Application.builder().token(TOKEN).build()

            async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
                await update.message.reply_text("🤖 Ocup-Killer v6.0 ONLINE\nEnvoie: Real Madrid vs Barcelona")

            async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
                txt = update.message.text
                if "vs" not in txt.lower():
                    await update.message.reply_text("Format: Equipe A vs Equipe B")
                    return
                a,b = [x.strip().title() for x in txt.split("vs",1)]
                await update.message.reply_text(f"⚙️ Calcul {a} vs {b}...")
                result = await asyncio.to_thread(bot_logic.analyze_sync, a, b)
                await update.message.reply_text(result)

            tg_app.add_handler(CommandHandler("start", start))
            tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

            async def process():
                await tg_app.initialize()
                await tg_app.process_update(Update.de_json(request.get_json(force=True), tg_app.bot))

            asyncio.run(process())
        except Exception as e:
            print(f"ERROR: {e}")
            return "error", 200
    return "WAR MACHINE ONLINE", 200
