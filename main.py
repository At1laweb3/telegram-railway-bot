import logging
import json
import os
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Logging
logging.basicConfig(level=logging.INFO)

# Učitaj Google Credentials iz Railway promeljive
creds_json = os.environ.get("GOOGLE_CREDS")
if creds_json is None:
    raise ValueError("GOOGLE_CREDS environment variable not set!")

creds_dict = json.loads(creds_json)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Zameni naziv sa stvarnim imenom tvog Google Sheet-a
sheet = client.open("ForexBotUsers").sheet1

# Koraci u konverzaciji
ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, ASK_PHONE = range(4)
user_data_store = {}

# Start komanda
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Dobrodošao! 👋\n\n"
        "Mi smo Forex tim koji pruža dnevne analize i tačne signale za trgovanje. 📈\n\n"
        "Da bismo te dodali u našu Telegram grupu, hajde da te upoznamo.\n\n"
        "Kako se zoveš?"
    )
    return ASK_NAME

# Ime korisnika
async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text("Hvala! Unesi svoj email:")
    return ASK_EMAIL

# Email korisnika
async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id]["email"] = update.message.text
    keyboard = [["Yes, that's correct", "I want to change it"]]
    await update.message.reply_text(
        f"Potvrdite email: {update.message.text}",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONFIRM_EMAIL

# Potvrda emaila
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "I want to change it":
        await update.message.reply_text("U redu, unesi ponovo svoj email:")
        return ASK_EMAIL

    keyboard = [[KeyboardButton("Podeli svoj broj", request_contact=True)]]
    await update.message.reply_text(
        "Odlično! Sada klikni dugme ispod da podeliš svoj broj telefona:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return ASK_PHONE

# Broj telefona
async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    user_data_store[update.effective_user.id]["phone"] = contact.phone_number

    data = user_data_store[update.effective_user.id]
    sheet.append_row([data["name"], data["email"], data["phone"]])

    await update.message.reply_text("Hvala! ✅\nEvo pozivnog linka za grupu:\nhttps://t.me/ASforexteamfree")
    return ConversationHandler.END

# Prekidanje
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Prekinuto. Ako želiš da počneš ponovo, pošalji /start.")
    return ConversationHandler.END

# Glavna funkcija
def main():
    application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            CONFIRM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.CONTACT, finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
