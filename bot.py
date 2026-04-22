import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# কনফিগারেশন
BOT_TOKEN = os.getenv("BOT_TOKEN")  # রেন্ডার এনভায়রনমেন্ট ভেরিয়েবল থেকে নিবে
ADMIN_ID = 8508012498
DB_NAME = "users.db"

# ডাটাবেজ ফাংশন
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

# ব্রডকাস্ট মোডের জন্য গ্লোবাল ভেরিয়েবল (মেমরিতে রাখা)
broadcast_mode = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)  # ইউজারকে ডাটাবেজে সংরক্ষণ

    # বাটন তৈরী
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

    message_text = (
        "👉👉 anyone buy group/channels dm me : @A15287 👈👈\n\n"
        "নিচের বাটনগুলোতে ক্লিক করে কন্টেন্ট দেখুন:"
    )
    await update.message.reply_text(message_text, reply_markup=reply_markup)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_mode
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("আপনি এই কমান্ড ব্যবহার করার অনুমতি রাখেন না।")
        return

    broadcast_mode = not broadcast_mode
    if broadcast_mode:
        await update.message.reply_text(
            "📢 Broadcast mode ON\n\n"
            "এখন আপনি যা কিছু পাঠাবেন, তা ডাটাবেজের সব ইউজারের কাছে ফরওয়ার্ড হবে।\n"
            "বন্ধ করতে আবার /admin দিন।"
        )
    else:
        await update.message.reply_text("🔕 Broadcast mode OFF")

async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_mode
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or not broadcast_mode:
        return  # শুধু অ্যাডমিন এবং ব্রডকাস্ট মোড অন থাকলেই কাজ করবে

    # কমান্ড আবার পাঠালে টগল করবে, সেটা ইতিমধ্যে admin_command এ হ্যান্ডেল করা
    if update.message.text and update.message.text.startswith('/'):
        return  # অন্যান্য কমান্ড ইগনোর করো

    message = update.message
    users = get_all_users()
    success_count = 0
    fail_count = 0

    for uid in users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=message.chat_id, message_id=message.message_id)
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send to {uid}: {e}")
            # যদি ইউজার বটকে ব্লক করে থাকে বা ইউজার ডিলিট হয়, তাহলে ডাটাবেজ থেকে মুছে ফেলা ভালো
            if "chat not found" in str(e).lower() or "user deactivated" in str(e).lower():
                remove_user(uid)
            fail_count += 1

    await update.message.reply_text(f"✅ ব্রডকাস্ট সম্পন্ন!\nসফল: {success_count}\nব্যর্থ: {fail_count}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ইনলাইন বাটনগুলোর জন্য কোনো callback data নেই, কারণ সব url বাটন, তাই এই ফাংশন প্রয়োজন নাও হতে পারে
    # তবে যদি ভবিষ্যতে callback data যোগ করা হয়, তাহলে হ্যান্ডেল করতে রাখা হলো
    query = update.callback_query
    await query.answer()

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    # ব্রডকাস্ট মেসেজ হ্যান্ডেলার: শুধু টেক্সট মেসেজ (এবং অন্যান্য টাইপ) অ্যাডমিনের কাছ থেকে
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_handler), group=1)
    # কমান্ড ছাড়া অন্য যেকোনো মেসেজ টাইপের জন্যও (যেমন ফটো, ভিডিও) ব্রডকাস্ট করতে চাইলে:
    # app.add_handler(MessageHandler(~filters.COMMAND, broadcast_handler), group=1)

    # বাটনে ক্লিক করার জন্য (যদিও url বাটনে কোনো callback_data নেই, তবুও রাখা হলো)
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot started with polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
