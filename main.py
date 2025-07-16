
import logging
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Konstantne vrednosti za korake
IME, EMAIL, POTVRDA, TELEFON = range(4)

# Učitaj Google credentials iz Railway promenljive
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDENTIALS_JSON")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(GOOGLE_CREDS), scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Zdravo! 👋
Dobrodošao u AS Forex tim.

Pošalji mi svoje ime kako bismo krenuli.")
    return IME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ime"] = update.message.text
    await update.message.reply_text("Super! 💬
Sada mi reci svoj email kako bismo ostali u kontaktu 📨👇")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    emails = sheet.col_values(2)
    if email in emails:
        await update.message.reply_text("⚠️ Ovaj email je već registrovan. Molimo te unesi drugi email.")
        return EMAIL
    context.user_data["email"] = email
    keyboard = [
        [
            InlineKeyboardButton("Da, tačan je", callback_data="correct"),
            InlineKeyboardButton("Želim da promenim", callback_data="change"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Unet email: {email}

Da li je tačan?", reply_markup=reply_markup
    )
    return POTVRDA

async def potvrda_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "correct":
        keyboard = [[KeyboardButton("📱 Pošalji svoj broj telefona", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await query.edit_message_text("Super! 📞
Sada pošalji svoj broj telefona klikom na dugme ispod 👇")
        return TELEFON
    else:
        await query.edit_message_text("U redu, pošalji ispravan email 📧")
        return EMAIL

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    telefon = contact.phone_number if contact else update.message.text

    context.user_data["telefon"] = telefon

    sheet.append_row([context.user_data["ime"], context.user_data["email"], telefon])

    await update.message.reply_text(
        f"Hvala! ✅
Evo linka za pristup grupi:
https://t.me/ASforexteamfree"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Prekinuto. Ako želiš da kreneš ponovo, pošalji /start.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            IME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            POTVRDA: [CallbackQueryHandler(potvrda_email)],
            TELEFON: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
