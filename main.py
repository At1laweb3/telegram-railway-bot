import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)

TOKEN = os.getenv("BOT_TOKEN")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

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

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    user_data_store[update.effective_user.id]["email"] = email

    keyboard = [
        [InlineKeyboardButton("Yes, that’s correct", callback_data="email_correct")],
        [InlineKeyboardButton("I want to change it", callback_data="email_wrong")]
    ]

    await update.message.reply_text(
        f"Great! Is your email address correct?\n\n{email}\n\nPlease confirm by choosing one of the options below. 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRM_EMAIL

async def handle_email_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "email_correct":
        await query.edit_message_text("Thanks, Boss, let's continue! 😎\n\nSada mi pošalji svoj broj telefona klikom na dugme ispod ☎️👇")

        keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📲 Pošalji moj broj", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
        await query.message.reply_text("Klikni ispod da pošalješ svoj broj:", reply_markup=keyboard)
        return ASK_PHONE

    elif query.data == "email_wrong":
        await query.edit_message_text("U redu, napiši ispravnu email adresu. 👇")
        return ASK_EMAIL

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone_number = contact.phone_number
    user_id = update.effective_user.id

    user_data_store[user_id]["phone"] = phone_number

    name = user_data_store[user_id]["name"]
    email = user_data_store[user_id]["email"]

    sheet.append_row([name, email, phone_number])

    invite_link = "https://t.me/ASforexteamfree"

    await update.message.reply_text(
        f"Hvala, sve je gotovo! ✅\n\nSada se priključi našoj ekskluzivnoj grupi klikom na link ispod 👇\n\n{invite_link}",
        reply_markup=ReplyKeyboardMarkup([["✅ Join the group"]], resize_keyboard=True)
    )
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            CONFIRM_EMAIL: [CallbackQueryHandler(handle_email_confirm)],
            ASK_PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
