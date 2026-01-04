import csv
import random
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# توکن رباتت را اینجا بگذار (بعداً حتماً از متغیر محیطی استفاده کن)
BOT_TOKEN = "8518152374:AAEBLJ42gvglQskz1J0xJduOxlW3hIfEdc0"

BASE_DIR = Path(__file__).resolve().parent
USERS_CSV = BASE_DIR / "users.csv"
MESSAGES_CSV = BASE_DIR / "messages.csv"

EMOJIS = [
    "😀", "😃", "😄", "😁", "😆", "😅",
    "😂", "🤣", "😊", "😍", "🤩", "😎",
    "🤖", "👾", "🐱", "🐶", "🐼", "🐧",
    "🍀", "🔥", "⭐", "🌈", "⚡", "🎲",
]


def init_csv_files() -> None:
    if not USERS_CSV.exists():
        with USERS_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "user_id",
                "username",
                "first_name",
                "last_name",
                "language_code",
                "first_seen_at",
                "last_seen_at",
            ])

    if not MESSAGES_CSV.exists():
        with MESSAGES_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "message_id",
                "user_id",
                "chat_id",
                "chat_type",
                "date",
                "text",
                "message_type",
            ])


def upsert_user(update: Update) -> None:
    user = update.effective_user
    if user is None:
        return

    now = datetime.utcnow().isoformat()

    rows = []
    found = False

    if USERS_CSV.exists():
        with USERS_CSV.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

    for row in rows:
        if row["user_id"] == str(user.id):
            row["username"] = user.username or ""
            row["first_name"] = user.first_name or ""
            row["last_name"] = user.last_name or ""
            row["language_code"] = user.language_code or ""
            row["last_seen_at"] = now
            found = True
            break

    if not found:
        rows.append({
            "user_id": str(user.id),
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "language_code": user.language_code or "",
            "first_seen_at": now,
            "last_seen_at": now,
        })

    with USERS_CSV.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "user_id",
            "username",
            "first_name",
            "last_name",
            "language_code",
            "first_seen_at",
            "last_seen_at",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def log_message(update: Update) -> None:
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if msg is None or user is None or chat is None:
        return

    if msg.text:
        message_type = "text"
        text = msg.text
    elif msg.sticker:
        message_type = "sticker"
        text = msg.sticker.emoji or ""
    elif msg.photo:
        message_type = "photo"
        text = ""
    else:
        message_type = "other"
        text = ""

    with MESSAGES_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            msg.message_id,
            user.id,
            chat.id,
            chat.type,
            msg.date.isoformat() if msg.date else "",
            (text or "").replace("\n", "\\n"),
            message_type,
        ])


async def start_command(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
    upsert_user(update)
    log_message(update)

    emoji = random.choice(EMOJIS)
    await update.message.reply_text(
        "✅" + emoji
    )


async def random_emoji_reply(update: Update,
                             context: ContextTypes.DEFAULT_TYPE) -> None:
    upsert_user(update)
    log_message(update)

    emoji = random.choice(EMOJIS)
    await update.message.reply_text(emoji)


def main() -> None:
    init_csv_files()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.ALL, random_emoji_reply))

    print("Bot is running... Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()
