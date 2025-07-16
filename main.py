import logging
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# States
ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, ASK_PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Zdravo! 👋\nDobrodošao u Forex tim!\n\nKako se zoveš? ✍️"
    )
    return ASK_NAME

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "Sada mi reci svoj email kako bismo ostali u kontaktu 📨👇"
    )
    return ASK_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    context.user_data["email"] = email

    # Check for duplicate email
    existing_emails = sheet.col_values(2)
    if email in existing_emails:
        await update.message.reply_text("Ova email adresa je već registrovana! ❌")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("Yes, that's correct", callback_data="yes_email"),
            InlineKeyboardButton("I want to change it", callback_data="no_email"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Da li je ovo tačan email?\n\n{email}", reply_markup=reply_markup
    )
    return CONFIRM_EMAIL

async def change_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("U redu, molim te unesi ispravnu email adresu: ✍️")
    return ASK_EMAIL

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Super! 📞\nSada pošalji svoj broj telefona klikom na dugme ispod:")

    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Pošalji svoj broj", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Klikni na dugme ispod da pošalješ svoj broj telefona.",
        reply_markup=contact_keyboard,
    )
    return ASK_PHONE

async def save_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone_number = contact.phone_number
    name = context.user_data.get("name")
    email = context.user_data.get("email")

    # Save to Google Sheet
    sheet.append_row([name, email, phone_number])

    await update.message.reply_text(
        "✅ Uspešno si se prijavio!\nEvo linka za pristup grupi:\nhttps://t.me/ASforexteamfree",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prekidam prijavu. Ako želiš ponovo, pošalji /start.")
    return ConversationHandler.END

if __name__ == "__main__":
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            CONFIRM_EMAIL: [
                CallbackQueryHandler(ask_phone, pattern="^yes_email$"),
                CallbackQueryHandler(change_email, pattern="^no_email$"),
            ],
            ASK_PHONE: [MessageHandler(filters.CONTACT, save_data)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()
