import random

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

# توکن ربات که از BotFather گرفتی:
BOT_TOKEN = "8518152374:AAEBLJ42gvglQskz1J0xJduOxlW3hIfEdc0"

# لیست ایموجی‌ها
EMOJIS = [
    "😀", "😃", "😄", "😁", "😆", "😅",
    "😂", "🤣", "😊", "😍", "🤩", "😎",
    "🤖", "👾", "🐱", "🐶", "🐼", "🐧",
    "🍀", "🔥", "⭐", "🌈", "⚡", "🎲"
]

async def random_emoji_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # انتخاب شانسی یک ایموجی
    emoji = random.choice(EMOJIS)
    await update.message.reply_text(emoji)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # هر نوع پیام را بگیریم و جواب ایموجی بدهیم
    application.add_handler(MessageHandler(filters.ALL, random_emoji_reply))

    print("Bot is running... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
