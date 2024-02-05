import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load bot info from .env
load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Commands handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Ciao, sono Caccometro. Manda 💩 quando hai fatto il tuo dovere.')

# Messages handlers
def handle_response(text: str) -> str:
    processed: str = text.lower()

    if '💩' in processed:
        return 'Bravo!'
    else:
        return 'Che noia, dimmi qualcosa di più interessante!'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    
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