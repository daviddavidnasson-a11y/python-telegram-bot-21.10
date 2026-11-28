
import os
import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")

if not BASE_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL is missing")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to DavidAntiBugBot!\n\n"
        "I help identify suspicious messages and scam warning signs.\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show commands\n"
        "/analyze - Analyze a message\n\n"
        "Send me a message to check it."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "DAVID ANTIBUG BOT\n\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/analyze - Analyze text\n\n"
        "Send a suspicious message to check it."
    )


def analyze_text(message):
    warnings = []
    text = message.lower()

    suspicious_words = [
        "send your password",
        "share your otp",
        "verify your account immediately",
        "claim your prize",
        "you have won",
        "urgent payment",
        "send your bank details",
        "account will be blocked",
        "click here to claim",
    ]

    for word in suspicious_words:
        if word in text:
            warnings.append(f"Suspicious phrase: {word}")

    if re.search(r"https?://", text):
        warnings.append("Contains a web link. Check its destination carefully.")

    if re.search(r"\b(bit\.ly|tinyurl\.com|cutt\.ly)\b", text):
        warnings.append("Contains a shortened link.")

    if re.search(r"\b(password|otp|pin|bank details)\b", text):
        warnings.append("Mentions sensitive account information.")

    if len(message) > 3000:
        warnings.append("Unusually long message.")

    return warnings


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = " ".join(context.args)

    if not message and update.message.reply_to_message:
        message = update.message.reply_to_message.text or ""

    if not message:
        await update.message.reply_text(
            "Send /analyze followed by a message, "
            "or reply to a message with /analyze."
        )
        return

    warnings = analyze_text(message)

    if warnings:
        result = "WARNING: Potentially suspicious message!\n\n"
        result += "\n".join(f"- {item}" for item in warnings)
        result += "\n\nThis is a basic warning check, not proof of fraud."
    else:
        result = (
            "No obvious warning signs detected.\n\n"
            "This does not guarantee that the message or link is safe."
        )

    await update.message.reply_text(result)


async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text or ""
    warnings = analyze_text(message)

    if warnings:
        await update.message.reply_text(
            "DavidAntiBugBot alert!\n\n"
            + "\n".join(f"- {item}" for item in warnings)
            + "\n\nPlease be careful."
        )


async def post_init(app: Application):
    await app.bot.set_webhook(
        url=f"{BASE_URL}/{TOKEN}",
        drop_pending_updates=True,
    )


def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, check_message)
    )

    print("DavidAntiBugBot is starting...")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{BASE_URL}/{TOKEN}",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
