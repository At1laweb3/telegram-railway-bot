
import logging
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# States
NAME, EMAIL, EMAIL_CONFIRM, PHONE = range(4)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Zdravo! Dobrodošao u AS Forex grupu!

"
        "Odmah ćemo te registrovati za potpuno BESPLATAN pristup našoj FREE grupi gde svakodnevno:

"
        "🔁 Automatski delimo naše rezultate
"
        "📸 Objavljujemo uspehe članova (preko 5,000 zadovoljnih!)
"
        "⚡️ Dajemo pravovremene signale
"
        "📈 Edukujemo i vodimo te kroz tvoj trading napredak

"
        "Ako poželiš još veći napredak, postoji i VIP opcija (Ukucaj /VIP ili se javi porukom profilu @) "
        "koja ti omogućava da KOPIRAŠ sve naše trejdove automatski — bez dodatnog truda.
"
        "✅ Potreban ti je samo telefon, 5 minuta dnevno i internet!

"
        "Krenimo sa registracijom! Kako se zoveš? 👇"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Sada mi reci svoj email kako bismo ostali u kontaktu 📩👇")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    all_records = sheet.get_all_records()
    if any(record["Email"] == email for record in all_records):
        await update.message.reply_text("Ovaj email je već registrovan! 🚫 Molimo unesi drugi email.")
        return EMAIL
    context.user_data["email"] = email
    keyboard = [["Yes, that's correct", "I want to change it"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(f"Da li je ovo tvoj email: {email}?", reply_markup=reply_markup)
    return EMAIL_CONFIRM

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = update.message.text
    if response == "I want to change it":
        await update.message.reply_text("U redu, unesi novi email:")
        return EMAIL
    contact_button = KeyboardButton("Podeli kontakt ☎️", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Odlično! Sada mi pošalji svoj broj telefona klikom na dugme ispod:", reply_markup=reply_markup)
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.contact.phone_number if update.message.contact else update.message.text
    name = context.user_data["name"]
    email = context.user_data["email"]
    sheet.append_row([name, email, phone_number])
    await update.message.reply_text("✅ Hvala! Evo linka za pristup grupi: https://t.me/ASforexteamfree")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registracija je otkazana. Ako želiš da pokušaš ponovo, pošalji /start.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            EMAIL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            PHONE: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
