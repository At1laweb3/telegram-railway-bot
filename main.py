from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

# Bot token
BOT_TOKEN = "7994996337:AAE7_WG5Rrq8lrAyKu-718S2rOar1EJPNG0"

# States
NAME, EMAIL, CONFIRM_EMAIL, PHONE = range(4)
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Započni ✅", callback_data="start_signup")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo="https://i.imgur.com/YOUR_IMAGE.png",  # zameni sa stvarnim linkom
        caption=(
            "👋 Dobrodošao!\n\n"
            "Mi smo tim koji se bavi Forexom preko 8 godina i imamo više od 5000 zadovoljnih studenata. 📈\n"
            "Iz dana u dan kačimo profite naših članova!\n\n"
            "Klikni na dugme ispod da započnemo!"
        ),
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data_store[query.from_user.id] = {}
    await query.message.reply_text("Kako se zoveš? 👇")
    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if any(prefix in name.lower() for prefix in ["zovem se", "ja sam", "moje ime je"]):
        name = re.sub(r"(?i)zovem se|ja sam|moje ime je", "", name).strip()

    user_data_store[update.effective_user.id]["name"] = name
    await update.message.reply_text(
        f"Super!\nSada mi reci svoj email kako bismo ostali u kontaktu 📧👇"
    )
    return EMAIL

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    existing_emails = sheet.col_values(2)
    if email in existing_emails:
        await update.message.reply_text("❌ Taj email je već iskorišćen. Molim te unesi drugi.")
        return EMAIL

    user_data_store[update.effective_user.id]["email"] = email
    keyboard = [["✅ Da, tačan je", "🔁 Želim da promenim email"]]
    await update.message.reply_text(
        f"✅ Da li je ovo tačan email?\n{email}",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "promenim" in update.message.text.lower():
        await update.message.reply_text("U redu, unesi novi email: 📧")
        return EMAIL
    else:
        contact_button = KeyboardButton("📞 Pošalji svoj broj", request_contact=True)
        await update.message.reply_text(
            "Skoro smo gotovi!\nKlikni ispod da pošalješ broj telefona:",
            reply_markup=ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True)
        )
        return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number
    user_id = update.effective_user.id
    name = user_data_store[user_id].get("name", "")
    email = user_data_store[user_id].get("email", "")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([name, email, phone, timestamp])

    invite_link = "https://t.me/ASforexteamfree"
    await update.message.reply_text(
        f"Hvala {name}, uspešno si se prijavio ✅\nKlikni ovde za ulazak u grupu:\n{invite_link}"
    )
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
            CONFIRM_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)],
            PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()
