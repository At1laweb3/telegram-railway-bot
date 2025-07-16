import logging
import json
import os
from datetime import datetime

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define conversation states
ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, ASK_PHONE = range(4)

# Google Sheets Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = json.loads(os.getenv("GOOGLE_CREDS"))
client = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds, scope))
sheet = client.open("ForexBotUsers").sheet1

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    await update.message.reply_text(
        "👋 Pozdrav!\n\n"
        "Dobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\n"
        "Iz dana u dan kačimo profite naših članova!\n\n"
        "Pocnimo!\nKako se zoveš? 👇"
    )
    return ASK_NAME

# Name handler
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        "Super!\nSada mi reci svoj email kako bismo ostali u kontaktu 📧👇"
    )
    return ASK_EMAIL

# Email handler
async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    context.user_data["email"] = email
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Da, tačno je", callback_data="email_correct"),
            InlineKeyboardButton("✏️ Želim da promenim", callback_data="email_change")
        ]
    ])
    await update.message.reply_text(
        f"Samo da proverimo, unet email: {email} 📧\n\nDa li je ovo tačno?",
        reply_markup=keyboard
    )
    return CONFIRM_EMAIL

# Callback query handler for email confirmation
async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "email_correct":
        contact_button = KeyboardButton("📱 Pošalji broj telefona", request_contact=True)
        contact_keyboard = ReplyKeyboardMarkup(
            [[contact_button]], resize_keyboard=True, one_time_keyboard=True
        )
        await query.message.reply_text(
            "Super!\nSada pošalji svoj broj telefona klikom na dugme ispod:",
            reply_markup=contact_keyboard
        )
        return ASK_PHONE
    else:
        await query.message.reply_text("U redu, unesi ponovo svoj email:")
        return ASK_EMAIL

# Phone handler
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.effective_message.contact
    phone = contact.phone_number

    name = context.user_data.get("name")
    email = context.user_data.get("email")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([name, email, phone, now])

    await update.message.reply_text(
        "✅ Hvala! Uspešno si se prijavio.\nOdmah dobijaš pristup grupi: https://t.me/ASforexteamfree",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Main function
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
            CONFIRM_EMAIL: [CallbackQueryHandler(confirm_email)],
            ASK_PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()
