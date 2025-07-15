from flask import Flask, request
import telegram

# --- DIREKTNO UBACEN TOKEN (test verzija) ---
TOKEN = "7994996937:AAE7_WG5Rrg8lrAyKu-718S2rOar1EJPNG0"
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!'

@app.route(f'/{TOKEN}', methods=['POST'])
def respond():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    if update.message:
        chat_id = update.message.chat.id
        text = update.message.text

        if text == "✅":
            bot.send_message(chat_id=chat_id, text="You sent a checkmark!")
        else:
            bot.send_message(chat_id=chat_id, text="I received your message!")

    return 'ok'

@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    webhook_url = f"https://{request.host}/{TOKEN}"
    success = bot.set_webhook(url=webhook_url)
    return f"Webhook setup: {success}"

if __name__ == "__main__":
    app.run(port=8080)
