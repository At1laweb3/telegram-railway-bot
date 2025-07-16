import logging
import datetime
import os
import json
from io import StringIO
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets autorizacija preko environment variable
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
if credentials_json is None:
    raise ValueError("GOOGLE_CREDENTIALS_JSON env variable not set!")
creds_dict = json.loads(credentials_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# Statička Telegram grupa invite veza
GROUP_INVITE_LINK = "https://t.me/ASforexteamfree"

# Inicijalizacija Logger-a
logging.basicConfig(level=logging.INFO)

# Koraci konverzacije
NAME, EMAIL, CONFIRM_EMAIL, PHONE = range(4)

# Privremeno skladište korisničkih podataka
user_data_store = {}

# /start komanda
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Pozdrav!\n\nDobrodošao! Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\nIz dana u dan kačimo profite naših članova!\n\nPočnimo!\nKako se zoveš? 👇"
    )
    return NAME

# Ime korisnika
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data_store[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text(
        f"Super!\nSada mi reci svoj email kako bismo ostali u kontaktu 📧👇"
    )
    return EMAIL

# Provera emaila
def is_valid_email(email: str) -> bool:
    import re
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# Email korisnika
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if not is_valid_email(email):
        await update.message.reply_text("⚠️ Molimo unesite validan email (npr. ime@email.com):")
        return EMAIL

    # Provera da li email već postoji
    all_emails = sheet.col_values(2)
    if email in all_emails:
        await update.message.reply_text("❗ Ovaj email je već registrovan. Molimo unesite drugi email:")
        return EMAIL

    user_data_store[update.effective_user.id]["email"] = email

    keyboard = [
        [InlineKeyboardButton("✅ Da, tačan je", callback_data="yes"),
         InlineKeyboardButton("🔁 Želim da promenim", callback_data="no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Potvrdite da je ovo vaš email:\n*{email}*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return CONFIRM_EMAIL

# Potvrda emaila
async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        keyboard = [[KeyboardButton("📱 Pošalji svoj broj telefona", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.edit_message_text("📾 Pošalji mi svoj broj telefona klikom na dugme ispod:")
        await context.bot.send_message(chat_id=query.from_user.id, text="⬇️", reply_markup=reply_markup)
        return PHONE
    else:
        await query.edit_message_text("🔁 Unesi novi email:")
        return EMAIL

# Kontakt korisnika
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    user_id = update.effective_user.id
    user_data = user_data_store.get(user_id)

    if contact and user_data:
        name = user_data["name"]
        email = user_data["email"]
        phone = contact.phone_number
        timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

        # Dodavanje u Google Sheet
        sheet.append_row([name, email, phone, timestamp])

        # Poruka i pozivni link
        await update.message.reply_text(
            f"Hvala {name}! ✅\nEvo linka za pristup grupi:\n{GROUP_INVITE_LINK}",
        )
    else:
        await update.message.reply_text("⚠️ Greška pri unosu podataka. Pokušajte ponovo.")
    return ConversationHandler.END

# Prekidanje komande
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Prekinuto. Ako želiš da kreneš ispočetka, pošalji /start")
    return ConversationHandler.END

if __name__ == "__main__":
    application = ApplicationBuilder().token("7994996337:AAE7_WG5Rrq8lrAyKu-718S2rOar1EJPNG0").build()

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

    application.add_handler(conv_handler)
    application.run_polling()
