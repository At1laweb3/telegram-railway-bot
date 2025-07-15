import logging
import json
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(os.getenv("GOOGLE_CREDS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# Logging
logging.basicConfig(level=logging.INFO)

# Conversation states
NAME, EMAIL, CONFIRM_EMAIL, PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Pozdrav! Dobrodošao u Forex tim.\n\nKako se zoveš?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("✉️ Unesi svoj email:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text(
        f"✅ Da li je ovaj email tačan?\n\n{context.user_data['email']}",
        reply_markup=ReplyKeyboardMarkup(
            [["Da, tačan je", "Želim da ga promenim"]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Želim da ga promenim":
        await update.message.reply_text("🔁 Unesi ponovo svoj email:")
        return EMAIL
    await update.message.reply_text(
        "📱 Pošalji broj telefona klikom na dugme ispod:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Pošalji kontakt", request_contact=True)]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.contact.phone_number
    context.user_data["phone"] = phone_number

    # Save to Google Sheet
    sheet.append_row([context.user_data["name"], context.user_data["email"], context.user_data["phone"]])

    await update.message.reply_text(
        "✅ Uspešno! Evo linka za pristup grupi:\nhttps://t.me/ASforexteamfree",
        reply_markup=None
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Proces otkazan.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            CONFIRM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
