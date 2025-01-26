import logging
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from asyncio import run_coroutine_threadsafe

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

QUOTES = [
    "Believe in yourself and all that you are.",
    "Your limitation—it’s only your imagination.",
    "Push yourself, because no one else is going to do it for you.",
    "Great things never come from comfort zones.",
    "Dream it. Wish it. Do it.",
    "Success doesn’t just find you. You have to go out and get it.",
    "The harder you work for something, the greater you’ll feel when you achieve it."
]

user_schedules = {}
scheduler = BackgroundScheduler()
scheduler.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and display the schedule menu."""
    keyboard = [
        [InlineKeyboardButton("Every 1 minute (test)", callback_data="1")],
        [InlineKeyboardButton("Every hour", callback_data="60")],
        [InlineKeyboardButton("Every 3 hours", callback_data="180")],
        [InlineKeyboardButton("Every 6 hours", callback_data="360")],
        [InlineKeyboardButton("Every 12 hours", callback_data="720")],
        [InlineKeyboardButton("Once a day", callback_data="1440")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Hi! I'm your Motivational Quotes Bot.\n"
        "Choose how often you'd like to receive motivational quotes:",
        reply_markup=reply_markup
    )

def send_quote(bot, chat_id, loop):
    coro = bot.send_message(chat_id=chat_id, text=random.choice(QUOTES))
    run_coroutine_threadsafe(coro, loop)


async def schedule_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    interval_minutes = int(query.data)

    # Удаляем существующую задачу для пользователя
    if chat_id in user_schedules:
        user_schedules[chat_id].remove()
        del user_schedules[chat_id]

    # Получаем текущий событийный цикл
    loop = asyncio.get_running_loop()

    # Добавляем новую задачу с передачей аргументов
    trigger = IntervalTrigger(minutes=interval_minutes)
    job = scheduler.add_job(
        send_quote,
        trigger,
        args=[context.bot, chat_id, loop]
    )
    user_schedules[chat_id] = job

    await query.edit_message_text(
        f"You've set your motivational quotes schedule to every {interval_minutes} minute(s)!\n"
        f"\n"
        f"Use /unset to clear your motivation schedule."
    )

async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unset the scheduled quote for the user."""
    chat_id = update.message.chat_id

    if chat_id in user_schedules:
        user_schedules[chat_id].remove()
        del user_schedules[chat_id]
        await update.message.reply_text("Your motivational quotes schedule has been cleared.")
    else:
        await update.message.reply_text("You don't have any schedule set.")

if __name__ == "__main__":
    # Create the bot application
    TOKEN = "8199372635:AAFgpgDhaJ05ttLCy5dNxx6LBy8kUEqIqUM"
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(schedule_quote))
    application.add_handler(CommandHandler("unset", unset))

    # Start the bot
    application.run_polling()
