import logging
import os
from datetime import datetime
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Google credentials from Railway environment variable
creds_json = os.getenv("GOOGLE_CREDS")
creds_dict = json.loads(creds_json)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# Bot stages
NAME, EMAIL, CONFIRM_EMAIL, PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        """👋 Pozdrav!

Dobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈
Iz dana u dan kačimo profite naših članova!

Počnimo!
Kako se zoveš? 👇"""
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text(
        "Super! \nSada mi reci svoj email kako bismo ostali u kontaktu 📧👇"
    )
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text.strip()
    reply_keyboard = [["Yes, that's correct", "I want to change it"]]
    await update.message.reply_text(
        f"Samo da proverimo, unet email: {context.user_data['email']} ✉️\n\nDa li je ovo tačno?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice == "Yes, that's correct":
        button = KeyboardButton("Podeli kontakt ☎️", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Super! \nSada pošalji svoj broj telefona klikom na dugme ispod:", reply_markup=reply_markup)
        return PHONE
    else:
        await update.message.reply_text("U redu, pošalji mi ponovo svoj email.")
        return EMAIL

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    phone = contact.phone_number if contact else update.message.text.strip()
    context.user_data['phone'] = phone

    name = context.user_data['name']
    email = context.user_data['email']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([name, email, phone, timestamp])

    await update.message.reply_text("✅ Hvala! Uspesno si se prijavio. Uskoro ćeš dobiti pristup grupi.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Registracija otkazana.")
    return ConversationHandler.END

def main() -> None:
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            CONFIRM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
