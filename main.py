import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)

TOKEN = os.getenv("BOT_TOKEN")

ASK_EMAIL, CONFIRM_EMAIL = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("👋 Zdravo! Dobrodošao!\n\nMolim te unesi svoj email:")
    return ASK_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["email"] = update.message.text.strip()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Da, tačan je", callback_data="confirm_yes")],
        [InlineKeyboardButton("❌ Nije tačan", callback_data="confirm_no")]
    ])

    await update.message.reply_text(
        f"📧 Potvrdi da li je ova e-mail adresa tačna:\n\n{context.user_data['email']}",
        reply_markup=keyboard
    )
    return CONFIRM_EMAIL

async def confirm_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_yes":
        group_link = "https://t.me/ASforexteamfree"
        await query.edit_message_text(
            f"🎉 Savršeno! Evo linka za ekskluzivnu grupu:\n{group_link}"
        )
        return ConversationHandler.END
    else:
        await query.edit_message_text("🔁 OK, unesi ponovo tačan e-mail:")
        return ASK_EMAIL

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Prekinuto.")
    return ConversationHandler.END

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            CONFIRM_EMAIL: [CallbackQueryHandler(confirm_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
