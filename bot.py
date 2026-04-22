import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8508012498
DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def add_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def remove_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

broadcast_mode = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    keyboard = [
        [InlineKeyboardButton("১. কঁচি বাচ্চাদের ভিডিও কালেকশন চ্যানেল", url="https://t.me/+GjG_tV4FHRc5OGY1")],
        [InlineKeyboardButton("২. ইংরেজিতে ভিডিও কালেকশন চ্যানেল", url="https://t.me/+1pQielc3rKw3ZWNl")],
        [InlineKeyboardButton("৩. হিন্দি ভিডিও কালেকশন চ্যানেল", url="https://t.me/+aitr4d3UVK9kOGVl")],
        [InlineKeyboardButton("৪. দেশি ভাইরাল ভিডিও টিকটকার কালেকশন চ্যানেল", url="https://t.me/+yhm_stb7aDNmZmZl")],
        [InlineKeyboardButton("৫. মুভি টাইপের কালেকশন ভিডিও", url="https://t.me/+WbqdfQLMvMU0YTA9")],
        [InlineKeyboardButton("৬. সাইট লিংক", url="https://bit.ly/hatia-viral-video-part1")],
        [InlineKeyboardButton("৭. গ্রুপ লিংক", url="https://t.me/+NjZfX0EyzTRlOWRl")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👉👉 anyone buy group/channels dm me : @A15287 👈👈\n\nনিচের বাটনে ক্লিক করুন:",
        reply_markup=reply_markup
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_mode
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("অনুমতি নেই।")
        return
    broadcast_mode = not broadcast_mode
    status = "ON" if broadcast_mode else "OFF"
    await update.message.reply_text(f"📢 Broadcast mode {status}\n{ 'এখন যেকোনো মেসেজ সবাই পাবে' if broadcast_mode else 'বন্ধ করা হয়েছে' }")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_mode
    if update.effective_user.id != ADMIN_ID or not broadcast_mode:
        return
    if update.message and update.message.text and update.message.text.startswith('/'):
        return
    message = update.message
    users = get_all_users()
    success = 0
    fail = 0
    for uid in users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=message.chat_id, message_id=message.message_id)
            success += 1
        except Exception:
            remove_user(uid)
            fail += 1
    await update.message.reply_text(f"✅ ব্রডকাস্ট শেষ!\nসফল: {success}\nব্যর্থ: {fail}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(MessageHandler(~filters.COMMAND, broadcast_handler), group=1)
    app.add_handler(CallbackQueryHandler(button_callback))
    logger.info("Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
