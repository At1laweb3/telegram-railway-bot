import logging
import json
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Google Sheets povezivanje
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.environ.get("GOOGLE_CREDS")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# Statičke vrednosti
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, ASK_PHONE = range(4)
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Zdravo! Dobrodošao u Forex Tim. Kako se zoveš?")
    return ASK_NAME

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text("Unesi svoj email:")
    return ASK_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id]["email"] = update.message.text
    keyboard = [["Da, tačan je", "Želim da ga promenim"]]
    await update.message.reply_text(
        f"Potvrdi email: {update.message.text}",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONFIRM_EMAIL

async def handle_email_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Želim da ga promenim":
        await update.message.reply_text("Unesi ponovo svoj email:")
        return ASK_EMAIL
    await update.message.reply_text(
        "Unesi broj telefona klikom na dugme ispod:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Pošalji broj", request_contact=True)]],
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone_number = update.message.contact.phone_number
    user = user_data_store.get(update.effective_user.id, {})
    user["phone"] = phone_number
    sheet.append_row([user.get("name", ""), user.get("email", ""), user.get("phone", "")])
    await update.message.reply_text(
        "Hvala! Evo ti link za našu Telegram grupu:\nhttps://t.me/ASforexteamfree"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Prekinuto. Ako želiš ponovo, pošalji /start.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            CONFIRM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_confirmation)],
            ASK_PHONE: [MessageHandler(filters.CONTACT, ask_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
