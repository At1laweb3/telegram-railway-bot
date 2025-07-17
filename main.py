import os
import logging
import json
from io import StringIO
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler, ContextTypes
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO)

NAME, EMAIL, CONFIRM_EMAIL, PHONE = range(4)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
creds_dict = json.loads(credentials_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Zdravo! 👋\nDobrodošao u AS Forex tim.\n\nDa bismo te dodali u tim, reci mi prvo kako se zoveš 👇")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Super! 💬\nSada mi reci svoj email kako bismo ostali u kontaktu 📩👇")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    existing_emails = sheet.col_values(2)[1:]  # skip header
    if email in existing_emails:
        await update.message.reply_text("⚠️ Ovaj email je već registrovan. Molimo pokušaj sa drugim emailom.")
        return EMAIL

    context.user_data["email"] = email

    keyboard = [
        [
            InlineKeyboardButton("✅ Da, tačan je", callback_data="yes"),
            InlineKeyboardButton("❌ Želim da ga promenim", callback_data="no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Da li je ovaj email tačan?\n\n{email}", reply_markup=reply_markup)
    return CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "yes":
        keyboard = [[KeyboardButton("📞 Pošalji kontakt", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.edit_message_text("Odlično! 📞\nSada pošalji svoj broj telefona klikom na dugme ispod:")
        await query.message.reply_text("Klikni ispod da podeliš broj telefona:", reply_markup=reply_markup)
        return PHONE
    else:
        await query.edit_message_text("U redu, napiši ispravnu email adresu 👇")
        return EMAIL

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    phone_number = contact.phone_number
    name = context.user_data["name"]
    email = context.user_data["email"]

    sheet.append_row([name, email, phone_number])

    await update.message.reply_text("Hvala! ✅\nEvo linka za pristup grupi:\nhttps://t.me/ASforexteamfree")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Prekinuto. Ako želiš da kreneš ispočetka, pošalji /start.")
    return ConversationHandler.END

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            CONFIRM_EMAIL: [CallbackQueryHandler(confirm_email)],
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
