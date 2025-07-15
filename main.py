import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# Setup logging
logging.basicConfig(level=logging.INFO)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# Conversation stages
NAME, EMAIL, EMAIL_CONFIRM, PHONE = range(4)

# Function to extract name from free text
def extract_name(text):
    # Remove common phrases
    text = text.lower()
    text = re.sub(r"ja se zovem|zovem se|moje ime je|zovem|ime mi je", "", text)
    return text.strip().title()

# Start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "📩 Pozdrav!\n\nDobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\nIz dana u dan kačimo profite naših članova!\n\nPočinimo!\nKako se zoveš? 👇"
    )
    return NAME

# Name handler
async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = extract_name(update.message.text)
    context.user_data["name"] = name
    await update.message.reply_text(
        f"Super, {name}! 🗫\nSada mi reci svoj email kako bismo ostali u kontaktu 📧👇"
    )
    return EMAIL

# Email handler
async def email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    context.user_data["email"] = email
    keyboard = [["Yes, that's correct", "I want to change it"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Tvoj email je: {email}?", reply_markup=reply_markup)
    return EMAIL_CONFIRM

# Email confirmation handler
async def email_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    if response == "Yes, that's correct":
        button = KeyboardButton("Pošalji svoj broj telefona 📱", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Super! Sada pošalji svoj broj klikom na dugme ispod:", reply_markup=reply_markup)
        return PHONE
    else:
        await update.message.reply_text("U redu, pošalji ispravan email:")
        return EMAIL

# Phone handler
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    phone = contact.phone_number
    name = context.user_data.get("name")
    email = context.user_data.get("email")
    sheet.append_row([name, email, phone])
    await update.message.reply_text("Hvala! Sada si zvanično deo naše zajednice! 🎉")
    return ConversationHandler.END

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Prekidam registraciju. Ako se predomisliš, samo kucaj /start.")
    return ConversationHandler.END

# Main function
def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_handler)],
            EMAIL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_confirm)],
            PHONE: [MessageHandler(filters.CONTACT, phone_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
