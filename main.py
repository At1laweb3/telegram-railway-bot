import os
from flask import Flask, request
import telegram

TOKEN = os.environ.get("TOKEN")
bot = telegram.Bot(token=TOKEN)
URL = f"https://web-production-0ec6c.up.railway.app"  # zameniti tvojim URL-om

app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    message = update.message.text

    if message == "/start":
        bot.send_message(chat_id=chat_id, text="👋 Hello! Bot is working fine.")

    return 'ok'

@app.route('/')
def index():
    return 'Bot is live!'

if __name__ == '__main__':
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
