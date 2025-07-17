import logging
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

NAME, EMAIL, CONFIRM_EMAIL, PHONE = range(4)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

async def start(update, context):
    await update.message.reply_text(
        """👋 Zdravo! Dobrodošao u AS Forex grupu!

Odmah ćemo te registrovati za potpuno BESPLATAN pristup našoj FREE grupi gde svakodnevno:

🔁 Automatski delimo naše rezultate  
📸 Objavljujemo uspehe članova (preko 5,000 zadovoljnih!)  
⚡️ Dajemo pravovremene signale  
📈 Edukujemo i vodimo te kroz tvoj trading napredak

Ako poželiš još veći napredak, postoji i VIP opcija (Ukucaj /VIP ili se javi porukom profilu @tvojprofil) koja ti omogućava da KOPIRAŠ sve naše trejdove automatski — bez dodatnog truda.  
✅ Potreban ti je samo telefon, 5 minuta dnevno i internet!

Krenimo sa registracijom! Kako se zoveš? 👇"""
    )
    return NAME

async def get_name(update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Unesi svoj email 👇")
    return EMAIL

async def get_email(update, context):
    email = update.message.text
    emails = sheet.col_values(2)
    if email in emails:
        await update.message.reply_text("Ova email adresa je već registrovana. Pokušaj sa drugom email adresom.")
        return EMAIL
    context.user_data["email"] = email
    buttons = [
        [InlineKeyboardButton("✅ Tačno je", callback_data="correct_email")],
        [InlineKeyboardButton("❌ Želim da promenim", callback_data="change_email")]
    ]
    await update.message.reply_text(
        f"Uneli ste email: {email}
Da li je tačan?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CONFIRM_EMAIL

async def confirm_email(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "correct_email":
        contact_button = KeyboardButton("📞 Pošalji svoj broj", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[contact_button]], one_time_keyboard=True, resize_keyboard=True)
        await query.edit_message_text("Klikni na dugme ispod da pošalješ svoj broj telefona 👇")
        await query.message.reply_text("📲", reply_markup=reply_markup)
        return PHONE
    else:
        await query.edit_message_text("U redu, unesi ponovo svoj email 👇")
        return EMAIL

async def get_phone(update, context):
    phone_number = update.message.contact.phone_number
    name = context.user_data["name"]
    email = context.user_data["email"]
    sheet.append_row([name, email, phone_number])
    await update.message.reply_text("✅ Uspešno si prijavljen!

Evo tvog linka za pristup grupi:
https://t.me/ASforexteamfree")
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("Registracija je otkazana.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
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

if __name__ == "__main__":
    main()
