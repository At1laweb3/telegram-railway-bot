import logging
import os
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes, CallbackQueryHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from io import StringIO

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states
NAME, EMAIL, EMAIL_CONFIRM, PHONE = range(4)

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# Load credentials from environment variable
google_creds_str = os.getenv("GOOGLE_CREDS_JSON")
google_creds_dict = json.loads(google_creds_str)
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Zdravo! Dobrodošao u AS Forex grupu!\n\n"
        "Odmah ćemo te registrovati za potpuno BESPLATAN pristup našoj FREE grupi gde svakodnevno:\n\n"
        "🔁 Automatski delimo naše rezultate\n"
        "📸 Objavljujemo uspehe članova (preko 5,000 zadovoljnih!)\n"
        "⚡️ Dajemo pravovremene signale\n"
        "📈 Edukujemo i vodimo te kroz tvoj trading napredak\n\n"
        "Ako poželiš još veći napredak, postoji i VIP opcija (Ukucaj /VIP ili se javi porukom profilu @) koja ti omogućava da KOPIRAŠ sve naše trejdove automatski — bez dodatnog truda.\n"
        "✅ Potreban ti je samo telefon, 5 minuta dnevno i internet!\n\n"
        "Krenimo sa registracijom! Kako se zoveš? 👇"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Unesi svoj email:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    context.user_data['email'] = email

    # Check for duplicates
    emails = sheet.col_values(2)
    if email in emails:
        await update.message.reply_text("Ova email adresa je već registrovana. Ako misliš da je greška, pokušaj sa drugom email adresom.")
        return EMAIL

    keyboard = [[
        InlineKeyboardButton("Da, tačan je ✅", callback_data="confirm_email"),
        InlineKeyboardButton("Želim da promenim ✏️", callback_data="change_email")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Uneli ste email: {email}\n\nDa li je tačan?", reply_markup=reply_markup
    )
    return EMAIL_CONFIRM

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_email":
        button = KeyboardButton("Podeli svoj kontakt ☎️", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)
        await query.edit_message_text("Pošalji svoj broj telefona klikom na dugme ispod:")
        await query.message.reply_text("⬇️ Klikni ispod", reply_markup=reply_markup)
        return PHONE
    else:
        await query.edit_message_text("U redu, unesi ponovo svoj email:")
        return EMAIL

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    phone_number = contact.phone_number

    name = context.user_data['name']
    email = context.user_data['email']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([name, email, phone_number, timestamp])

    await update.message.reply_text(
        "✅ Uspešno si registrovan!\n\nKlikni ispod za pristup našoj besplatnoj grupi:\nhttps://t.me/ASforexteamfree"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registracija otkazana.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            EMAIL_CONFIRM: [CallbackQueryHandler(confirm_email)],
            PHONE: [MessageHandler(filters.CONTACT, get_phone)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
