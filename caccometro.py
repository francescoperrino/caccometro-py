import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import STORING_FORMAT, initialize_database, get_count, update_count, get_rank, get_statistics
from utils import DISPLAY_FORMAT, CHARTS_FOLDER, generate_table_and_chart

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Load bot info from .env
load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    initialize_database(update.message.chat_id)
    await update.message.reply_text('Ciao, sono Caccometro. Manda 💩 quando hai fatto il tuo dovere.')

async def classifica_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_mese command."""
    args = context.args
    if args:
        try:
            month, year = args[0].split('-')
            date = f"{month}-{year}"
        except ValueError:
            await update.message.reply_text("Formato data non valido. Usa MM-YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        date = now.strftime("%m-%Y")

    rank = get_rank(update.message.chat_id, 'month', date)
    if not rank:
        await update.message.reply_text(f'Nel mese {date} non sono state contate 💩.')
        return

    message = f'Ecco la classifica del mese {date}:\n'
    for i, (username, total_count) in enumerate(rank, start=1):
        message += f"{i}. @{username}: {total_count}\n"

    generate_table_and_chart(rank, update.message.chat_id, 'month', date)

    date_parts = date.split('-')
    saving_date = f"{date_parts[1]}_{date_parts[0]}"

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{saving_date}.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message)

async def classifica_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_anno command."""
    args = context.args
    if args:
        year = args[0]
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        year = now.strftime("%Y")

    rank = get_rank(update.message.chat_id, 'year', year)
    if not rank:
        await update.message.reply_text(f'Nell\'anno {year} non sono state contate 💩.')
        return

    message = f'Ecco la classifica dell\'anno {year}:\n'
    for i, (username, total_count) in enumerate(rank, start=1):
        message += f"{i}. @{username}: {total_count}\n"

    generate_table_and_chart(rank, update.message.chat_id, 'year', year)

    with open(os.path.join(CHARTS_FOLDER, f'{update.message.chat_id}_{year}.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message)

async def statistiche_mese_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_mese command."""
    args = context.args
    if args:
        try:
            month, year = args[0].split('-')
            date = f"{month}-{year}"
        except ValueError:
            await update.message.reply_text("Formato data non valido. Usa MM-YYYY.")
            return
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        date = now.strftime("%m-%Y")

    statistics = get_statistics(update.message.chat_id, 'month', date)
    if not statistics:
        await update.message.reply_text(f'Nessuna statistica disponibile per il mese {date}.')
        return

    message = f'Statistiche per il mese {date}:\n'
    for i, stats in enumerate(statistics, start=1):
        message += f"{i}. @{stats['username']}: Media: {stats['mean']:.2f}, Varianza: {stats['variance']:.2f}\n"

    await update.message.reply_text(message)

async def statistiche_anno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /statistiche_anno command."""
    args = context.args
    if args:
        year = args[0]
    else:
        now = datetime.now(pytz.timezone('Europe/Rome'))
        year = now.strftime("%Y")

    statistics = get_statistics(update.message.chat_id, 'year', year)
    if not statistics:
        await update.message.reply_text(f'Nessuna statistica disponibile per l\'anno {year}.')
        return

    message = f'Statistiche per l\'anno {year}:\n'
    for i, stats in enumerate(statistics, start=1):
        message += f"{i}. @{stats['username']}: Media: {stats['mean']:.2f}, Varianza: {stats['variance']:.2f}\n"

    await update.message.reply_text(message)

async def aggiungi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /aggiungi command."""
    args = context.args
    if len(args) != 2 or not args[0].startswith('@'):
        await update.message.reply_text("Formato non valido. Usa: /aggiungi @username DD-MM-YYYY")
        return

    username = args[0][1:]  # Rimuovi il @
    date = args[1]

    try:
        parsed_date = datetime.strptime(date, "%d-%m-%Y")
        selected_date = parsed_date.strftime(STORING_FORMAT)
        today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
        if selected_date > today:
            raise ValueError("La data selezionata è nel futuro.")
    except ValueError as e:
        await update.message.reply_text(f"Errore: {str(e)}")
        return

    count = get_count(username, selected_date, update.message.chat_id)
    update_count(username, selected_date, count + 1, update.message.chat_id)
    await update.message.reply_text(
        f"Il conteggio di @{username} nel giorno {date} è stato aggiornato a {count + 1} 💩.")

async def togli_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /togli command."""
    args = context.args
    if len(args) != 2 or not args[0].startswith('@'):
        await update.message.reply_text("Formato non valido. Usa: /togli @username DD-MM-YYYY")
        return

    username = args[0][1:]
    date = args[1]

    try:
        parsed_date = datetime.strptime(date, "%d-%m-%Y")
        selected_date = parsed_date.strftime(STORING_FORMAT)
        today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
        if selected_date > today:
            raise ValueError("La data selezionata è nel futuro.")
    except ValueError as e:
        await update.message.reply_text(f"Errore: {str(e)}")
        return

    count = get_count(username, selected_date, update.message.chat_id)
    if count > 0:
        update_count(username, selected_date, count - 1, update.message.chat_id)
        await update.message.reply_text(
            f"Il conteggio di @{username} nel giorno {date} è stato aggiornato a {count - 1} 💩.")
    else:
        await update.message.reply_text(
            f"Il conteggio di @{username} nel giorno {date} non può essere aggiornato poiché era già 0 💩.")

async def conto_giorno_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /conto_giorno command."""
    args = context.args
    if args:
        try:
            date = datetime.strptime(args[0], "%d-%m-%Y").strftime(STORING_FORMAT)
        except ValueError:
            await update.message.reply_text("Formato data non valido. Usa DD-MM-YYYY.")
            return
    else:
        date = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)

    username = update.message.from_user.username
    count = get_count(username, date, update.message.chat_id)
    
    if count != 0:
        await update.message.reply_text(f"@{username} il giorno {args[0] if args else 'oggi'} hai fatto 💩 {count} {'volte' if count > 1 else 'volta'}.")
    else:
        await update.message.reply_text(f"@{username} il {args[0] if args else 'oggi'} non hai fatto 💩.")

# Messages handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for processing messages."""

    # Check if the message contains text and is not empty
    if not update.message or not update.message.text:
        return
    
    text: str = update.message.text.lower().strip()
    response: str = ''

    if BOT_USERNAME in text:
        response = 'Cosa vuoi dirmi?'

    if '💩' in text:
        username = update.message.from_user.username
        today = datetime.now(pytz.timezone('Europe/Rome')).strftime(STORING_FORMAT)
        update_count(username, today, get_count(username, today, update.message.chat_id) + 1, update.message.chat_id)
        response = f'Complimenti @{username}, oggi hai fatto 💩 {get_count(username, today, update.message.chat_id)} ' + (
            'volte' if get_count(username, today, update.message.chat_id) > 1 else 'volta') + '!'

    if 'run' in text:
        username = update.message.from_user.username
        response = f'@{username} cazzo scrivi Run, funziono solo con i comandi specifici e non quelli che ti inventi tu.'

    if response:
        await update.message.reply_text(response)

# Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for logging errors."""
    logger.error(f'Update "{update}" caused error "{context.error}"')

# Main function to handle bot interactions
"""Main function to start the bot."""

# Create the Application instance
if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('classifica_mese', classifica_mese_command))
    application.add_handler(CommandHandler('classifica_anno', classifica_anno_command))
    application.add_handler(CommandHandler('statistiche_mese', statistiche_mese_command))
    application.add_handler(CommandHandler('statistiche_anno', statistiche_anno_command))
    application.add_handler(CommandHandler('aggiungi', aggiungi_command))
    application.add_handler(CommandHandler('togli', togli_command))
    application.add_handler(CommandHandler('conto_giorno', conto_giorno_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)

    # Polling
    while True:
        try:
            application.run_polling(allowed_updates=Update.MESSAGE, drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Errore nel polling: {e}")