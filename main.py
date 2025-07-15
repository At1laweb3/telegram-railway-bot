import os
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ◆ 1.  ENV VAR
TOKEN = os.getenv("BOT_TOKEN")

# ◆ 2.  Stati za ConversationHandler-a
ASK_NAME, ASK_EMAIL, CONFIRM_EMAIL = range(3)

# ◆ 3.  /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Dobrodošao! Kako se zoveš?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


# ◆ 4.  Primamo ime
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        f"Drago mi je, {context.user_data['name']}!\n📧 Koja je tvoja e-mail adresa?"
    )
    return ASK_EMAIL


# ◆ 5.  Primamo e-mail + dugmad za potvrdu
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["email"] = update.message.text.strip()

    kb = ReplyKeyboardMarkup(
        [
            [KeyboardButton("✅ Tačan je"), KeyboardButton("❌ Nije tačan")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        f"Potvrdi da li je ovo tvoj e-mail:\n\n{context.user_data['email']}",
        reply_markup=kb,
    )
    return CONFIRM_EMAIL


# ◆ 6.  Obrada potvrde
async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()

    if choice.startswith("✅"):
        # —————  LINK do grupe  —————
        GROUP_LINK = "https://t.me/ASforexteamfree"
        # ————————————————
        await update.message.reply_text(
            f"🎉 Savršeno! Evo linka za ekskluzivnu grupu:\n{GROUP_LINK}",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    if choice.startswith("❌"):
        await update.message.reply_text("OK, unesi ispravan e-mail:")
        return ASK_EMAIL

    # Fallback (ako klikne nešto treće)
    await update.message.reply_text("Molim te izaberi ✅ ili ❌ 🙂")
    return CONFIRM_EMAIL


# ◆ 7.  /cancel (korisnik prekida)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Prekinuto. Slobodno pošalji /start kad god želiš da počnemo ponovo.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ◆ 8.  Glavna funkcija
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            CONFIRM_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_email)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
