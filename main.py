import os
import json
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Telegram bot token
TOKEN = os.getenv("BOT_TOKEN")

# Google Sheets connection
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.getenv("GOOGLE_CREDS_JSON")), scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# States for ConversationHandler
ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, ASK_PHONE = range(4)

user_data_store = {}

# Extract only name from text
def extract_name(raw_text):
    name_matches = re.findall(r"[A-ZŠĐČĆŽ][a-zšđčćž]+(?:\s+[A-ZŠĐČĆŽ][a-zšđčćž]+)+", raw_text)
    return name_matches[0] if name_matches else raw_text.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Pozdrav!\n\n"
        "Dobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\n"
        "Iz dana u dan kačimo profite naših članova!\n\n"
        "Pocnimo!\nKako se zoveš? 👇"
    )
    return ASK_NAME

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_name = update.message.text
    name = extract_name(raw_name)
    user_data_store[update.effective_user.id] = {"name":_]()
