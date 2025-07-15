import os
from flask import Flask, request
import telegram

TOKEN = os.environ.get("TOKEN")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    if update.message and update.message.text == "/start":
        bot.send_message(chat_id=update.message.chat_id, text="Bot is live and responding! ✅")
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    app.run(port=8080)
