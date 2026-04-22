import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
import uvicorn

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8508012498
DB_NAME = "users.db"

# ---------- ডাটাবেজ ----------
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

# ---------- ব্রডকাস্ট মোড ----------
broadcast_mode = False

# ---------- হ্যান্ডলার ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)

    keyboard = [
        [InlineKeyboardButton("1. কঁচি বাচ্চাদের ভিডিও 🥵💋🥵💋👉", url="https://t.me/+GjG_tV4FHRc5OGY1")],
        [InlineKeyboardButton("2. ইংরেজিতে ভিডিও কালেকশন 🥵💦👉🥵", url="https://t.me/+1pQielc3rKw3ZWNl")],
        [InlineKeyboardButton("3. হিন্দি ভিডিও চ্যানেল 🥵💦💋👉", url="https://t.me/+aitr4d3UVK9kOGVl")],
        [InlineKeyboardButton("4. দেশি ভাইরাল ভিডিও টিকটকার চ্যানেল 🫣☺️👉", url="https://t.me/+yhm_stb7aDNmZmZl")],
        [InlineKeyboardButton("5. মুভি টাইপের ভিড়িও 👉☺️💋💦", url="https://t.me/+WbqdfQLMvMU0YTA9")],
        [InlineKeyboardButton("6. সাইট লিংক 👉☺️💋💦", url="https://bit.ly/hatia-viral-video-part1")],
        [InlineKeyboardButton("7. গ্রুপ লিংক ☺️💋", url="https://t.me/+NjZfX0EyzTRlOWRl")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👉👉 anyone buy group/channels dm me : @A15287 👈👈\n\nনিচের বাটনগুলোতে ক্লিক করুন:",
        reply_markup=reply_markup
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_mode
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("অনুমতি নেই।")
        return
    broadcast_mode = not broadcast_mode
    if broadcast_mode:
        await update.message.reply_text(
            "📢 Broadcast mode ON\n\nAny message you send now will be delivered to all users."
        )
    else:
        await update.message.reply_text("🔕 Broadcast mode OFF")

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

# ---------- ওয়েবহুক ----------
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return Response(status_code=200)

async def health_check(request: Request):
    return PlainTextResponse("OK")

# ---------- মেইন ----------
bot_app = None

async def main():
    global bot_app
    init_db()
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("admin", admin_command))
    bot_app.add_handler(MessageHandler(~filters.COMMAND, broadcast_handler), group=1)
    bot_app.add_handler(CallbackQueryHandler(button_callback))
    await bot_app.initialize()

    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if not render_url:
        logger.error("RENDER_EXTERNAL_URL not set")
        return
    webhook_url = f"{render_url}/webhook"
    await bot_app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logger.info(f"Webhook set to {webhook_url}")

    starlette_app = Starlette(routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/health", health_check, methods=["GET"]),
    ])
    port = int(os.getenv("PORT", "8000"))
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
