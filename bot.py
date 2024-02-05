import os
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load bot info from .env
load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# 💩 counter for each user
user_poop_count = {}

# Commands handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Ciao, sono Caccometro. Manda 💩 quando hai fatto il tuo dovere.')

# Messages handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text.lower()
    response: str = ''

    if BOT_USERNAME in text:
        response = 'Cosa vuoi dirmi?'
    
    if '💩' in text:
        user_id = update.message.from_user.id
        today = datetime.now().date()
        user_poop_count.setdefault(user_id, {}).setdefault(today, 0)
        user_poop_count[user_id][today] += 1
        response = f'Bravo! Hai mandato 💩 {user_poop_count[user_id][today]} volte oggi.'
    
    await update.message.reply_text(response)

# Error
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Errore: {context.error}')

# Main
if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler('start', start_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)

    # Polling
    application.run_polling(poll_interval = 5)