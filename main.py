import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://YOUR-RAILWAY-URL.up.railway.app/{TOKEN}"  # zameni sa tvojim URL-om

app = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

# /start komanda
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot je uspešno pokrenut! 🚀")

# dodaj handler za /start
application.add_handler(CommandHandler("start", start))

# webhook endpoint
@app.route(WEBHOOK_PATH, methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok", 200

# webhook setup (radi samo jednom)
@app.before_first_request
def set_webhook():
    application.bot.set_webhook(url=WEBHOOK_URL)

# start Flask server
if __name__ == "__main__":
    app.run(port=8080)
