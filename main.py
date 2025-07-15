import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)

# Setup za Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("telegram-bot-sheet-466011-9e1d39b4b8cf.json", scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# Bot TOKEN iz okruženja
TOKEN = os.getenv("BOT_TOKEN")

ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, ASK_PHONE = range(4)

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Pozdrav!\n\n"
        "Dobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\n"
        "Iz dana u dan kačimo profite naših članova!\n\n"
        "Pocnimo!\nKako se zoveš? 👇"
    )
    return ASK_NAME

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user_data_store[update.effective_user.id] = {"name": name}
    await update.message.reply_text(f"Super, {name}! 💬\nSada mi reci svoj email kako bismo ostali u kontaktu 📧👇")
    return ASK_EMAIL

async def confirm_email(update: Update,_
