from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import gspread
import json
import os
from datetime import datetime

# Google Sheets autorizacija
google_creds = json.loads(os.environ["GOOGLE_CREDS"])
gc = gspread.service_account_from_dict(google_creds)
sh = gc.open("ForexBotUsers")
sheet = sh.sheet1

# Stati za ConversationHandler
ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL, GET_PHONE = range(4)

# Start komanda
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Pozdrav!\n\n"
        "Dobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\n"
        "Iz dana u dan kačimo profite naših članova!\n\n"
        "Počnimo!\nKako se zoveš? 👇"
    )
    return ASK_NAME

# Ime korisnika
async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Super!\nSada mi reci svoj email kako bismo ostali u kontaktu 📧👇")
    return ASK_EMAIL

# Email korisnika
async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text
    context.user_data["email"] = email

    await update.message.reply_text(
        f"📩 Samo da proverimo, unet email: {email}\n\n"
        "Da li je ovo tačno?",
        reply_markup=ReplyKeyboardMarkup(
            [["✅ Da, tačno je", "✏️ Želim da promenim"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return CONFIRM_EMAIL

# Provera emaila
async def handle_email_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if "tačno" in text.lower():
        return await ask_for_phone(update, context)
    else:
        await update.message.reply_text("U redu, pošalji mi ponovo svoj email 📧")
        return ASK_EMAIL

# Traženje broja telefona
async def ask_for_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Super! \nSada pošalji svoj broj telefona klikom na dugme ispod:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Pošalji svoj broj", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return GET_PHONE

# Prijem broja telefona i upis u Sheet
async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    user_data["phone"] = update.message.contact.phone_number
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([user_data["name"], user_data["email"], user_data["phone"], now])

    await update.message.reply_text(
        "✅ Hvala! Uspešno si se prijavio.\nKlikni na link ispod da pristupiš grupi:\n\n"
        "👉 https://t.me/ASforexteamfree",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Cancel komanda
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Prekidam prijavu. Ako poželiš ponovo, pošalji /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Pokretanje bota
app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
        ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
        CONFIRM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_confirmation)],
        GET_PHONE: [MessageHandler(filters.CONTACT, handle_phone)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(conv_handler)

if __name__ == "__main__":
    app.run_polling()
