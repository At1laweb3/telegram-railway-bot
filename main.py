
import os
from flask import Flask, request
import telegram

TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

user_state = {}

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text.strip() if update.message.text else ""

    if text == "/start":
        user_state[chat_id] = {"step": "ask_name"}
        bot.send_message(chat_id=chat_id, text="👋 Welcome! What's your name?")
    elif chat_id in user_state:
        step = user_state[chat_id]["step"]

        if step == "ask_name":
            user_state[chat_id]["name"] = text
            user_state[chat_id]["step"] = "ask_email"
            bot.send_message(chat_id=chat_id, text=f"Nice to meet you, {text}! What's your email?")
        elif step == "ask_email":
            user_state[chat_id]["email"] = text
            user_state[chat_id]["step"] = "confirm_email"
            keyboard = telegram.ReplyKeyboardMarkup(
                keyboard=[[telegram.KeyboardButton("✅ Yes"), telegram.KeyboardButton("❌ No")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            bot.send_message(chat_id=chat_id, text=f"Please confirm your email: {text}", reply_markup=keyboard)
        elif step == "confirm_email":
            if text == "✅ Yes":
                bot.send_message(chat_id=chat_id, text="Perfect! 🎉 Here's the group link:
👉 https://t.me/ASforexteamfree")
                user_state.pop(chat_id)
            elif text == "❌ No":
                user_state[chat_id]["step"] = "ask_email"
                bot.send_message(chat_id=chat_id, text="Okay, please enter your correct email:")

    return 'ok'

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    app.run(port=8080)
