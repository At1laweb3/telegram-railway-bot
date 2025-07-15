import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)

# Telegram bot token
TOKEN = os.getenv("BOT_TOKEN")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# Load credentials from Railway environment variable
credentials_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# States for conversation
ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, ASK_PHONE = range(4)

# Store user data during session
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Pozdrav!\n\n"
        "Dobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\n"
