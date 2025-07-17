import logging
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

# Google Sheets authorization
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("ForexBotUsers").sheet1

(
    NAME,
    EMAIL,
    CONFIRM_EMAIL,
    PHONE,
) = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Zdravo! Dobrodošao u AS Forex grupu!\n\n"
        "Odmah ćemo te registrovati za potpuno BESPLATAN pristup našoj FREE grupi gde svakodnevno:\n\n"
        "🔁 Automatski delimo naše rezultate\n"
        "📸 Objavljujemo uspehe članova (preko 5,000 zadovoljnih!)\n"
        "⚡️ Dajemo pravovremene signale\n"
        "📈 Edukujemo i vodimo te kroz tvoj trading napredak\n\n"
        "Ako poželiš još veći napredak, postoji i VIP opcija (Ukucaj /VIP ili se javi porukom profilu @) "
        "koja ti omogućava da KOPIRAŠ sve naše trejdove automatski — bez dodatnog truda.\n"
        "✅ Potreban ti je samo telefon, 5 minuta dnevno i internet!\n\n"
        "Krenimo sa registracijom! Kako se zoveš? 👇"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Unesi svoj email:")
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text

    # Check for duplicate email
    existing_emails = sheet.col_values(2)
    if email in existing_emails:
        await update.message.reply_text("⚠️ Ovaj email je već registrovan.")
        return ConversationHandler.END

    context.user_data["email"] = email
    await update.message.reply_text(
        f"Uneli ste email: {email}.\nDa li je tačan?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✔️ Da, tačan je", callback_data="email_yes")],
            [InlineKeyboardButton("❌ Želim da promenim", callback_data="email_change")]
        ])
    )
    return CONFIRM_EMAIL


async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "email_yes":
        await query.edit_message_text("Unesi svoj broj telefona (ili klikni dugme da podeliš kontakt):")
        keyboard = [[KeyboardButton("📱 Pošalji kontakt", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text("Podeli broj klikom ispod ili ukucaj ručno:", reply_markup=reply_markup)
        return PHONE
    else:
        await query.edit_message_text("Unesi ponovo svoj email:")
        return EMAIL


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data["phone"] = phone

    name = context.user_data["name"]
    email = context.user_data["email"]

    # Save data to Google Sheets
    sheet.append_row([name, email, phone])

    # Send group invite link
    await update.message.reply_text(
        "✅ Uspešno si se prijavio!\nKlikni ispod da se pridružiš našoj FREE grupi:\nhttps://t.me/ASforexteamfree"
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registracija je otkazana.")
    return ConversationHandler.END


def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            CONFIRM_EMAIL: [CallbackQueryHandler(confirm_email)],
            PHONE: [MessageHandler(filters.ALL, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
