import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from database import initialize_database, get_count, update_count, get_users, get_dates, get_rank, get_monthly_stats, get_yearly_stats
from utils import storing_format, display_format, charts_folder, generate_table_and_chart
import re

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Load bot info from .env
load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Define conversation states
USER_CHOICE, DAY_CHOICE, CONFIRM_CHOICE, DATE_CHOICE, CONFIRM_DATE_CHOICE, ERROR_CONVERSATION = range(6)

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    initialize_database(update.message.chat_id)
    await update.message.reply_text('Ciao, sono Caccometro. Manda 💩 quando hai fatto il tuo dovere.')

async def user_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handler for selecting a user to update poop count."""
    command = update.message.text
    context.user_data['command'] = command
    await update.message.reply_text(
        f'Hai scelto di {"incrementare" if "/aggiungi" in context.user_data["command"] else "ridurre"} il conteggio di 💩 a un utente.\n'
        'Se vuoi annullare, digita Annulla.')

    users = get_users(update.message.chat_id)
    if not users:
        await update.message.reply_text("Non può essere selezionato alcun utente, comando annullato!",
                                        reply_markup=ReplyKeyboardRemove())
        return ERROR_CONVERSATION
    else:
        if len(users) > 2:
            users_per_row = 2
            reply_keyboard = [users[i:i + users_per_row] for i in range(0, len(users), users_per_row)]
            reply_keyboard.append(["Annulla"])
        else:
            reply_keyboard = [users, ["Annulla"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Chi scegli?', reply_markup=markup)

        return DAY_CHOICE

async def day_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handler for selecting a date to update poop count."""
    user = update.message.text
    context.user_data['selected_user'] = user

    if context.user_data['selected_user'] not in get_users(update.message.chat_id):
        await update.message.reply_text("Hai inserito una scelta non valida, comando annullato!",
                                        reply_markup=ReplyKeyboardRemove())
        return ERROR_CONVERSATION

    await update.message.reply_text(f"Hai scelto @{context.user_data['selected_user']}!", reply_markup=ReplyKeyboardRemove())

    if '/aggiungi' in context.user_data['command']:
        await update.message.reply_text('Ora inserisci il giorno (in formato dd-mm-YYYY):')
    elif '/togli' in context.user_data['command']:
        dates = get_dates(context.user_data['selected_user'], update.message.chat_id)
        half_length = len(dates) // 2
        column1 = dates[:half_length]
        column2 = dates[half_length:]
        reply_keyboard = [column1, column2, ["Annulla"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Ora scegli il giorno:', reply_markup=markup)

    return CONFIRM_CHOICE

async def confirm_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for confirming the choice and updating the poop count."""
    date_text = update.message.text
    try:
        selected_date = datetime.strptime(date_text, display_format).strftime(storing_format)
        today = datetime.now(pytz.timezone('Europe/Rome')).strftime(storing_format)
        if selected_date > today:
            raise ValueError("La data selezionata è nel futuro.")
    except ValueError:
        await update.message.reply_text("Hai inserito una data non valida, comando annullato!",
                                        reply_markup=ReplyKeyboardRemove())
        return ERROR_CONVERSATION

    selected_user = context.user_data.get('selected_user', None)
    if selected_user is None:
        await update.message.reply_text("Utente non valido, comando annullato!",
                                        reply_markup=ReplyKeyboardRemove())
        return ERROR_CONVERSATION

    await update.message.reply_text(
        f"Hai scelto @{selected_user.lower()} e il giorno {date_text}.",
        reply_markup=ReplyKeyboardRemove())

    command = context.user_data.get('command', '')
    count = get_count(selected_user, selected_date, update.message.chat_id)
    if '/aggiungi' in command:
        update_count(selected_user, selected_date, count + 1, update.message.chat_id)
        await update.message.reply_text(
            f"Il conteggio di @{selected_user} nel giorno {date_text} è stato aggiornato a {count + 1} 💩.",
            reply_markup=ReplyKeyboardRemove())
    elif '/togli' in command:
        if count > 0:
            update_count(selected_user, selected_date, count - 1, update.message.chat_id)
            await update.message.reply_text(
                f"Il conteggio di @{selected_user} nel giorno {date_text} è stato aggiornato a {count - 1} 💩.",
                reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text(
                f"Il conteggio di @{selected_user} nel giorno {date_text} non può essere aggiornato poiché era già {count} 💩.",
                reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

async def date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Handler for selecting the date of the rank."""
    command = update.message.text
    context.user_data['command'] = command
    await update.message.reply_text(
        f'Hai scelto di mostrare la classifica {"mensile" if "/mese" in context.user_data["command"] else "annuale"}.\n'
        f'Inserisci il {"mese in formato mm-YYYY" if "/mese" in context.user_data["command"] else "l\'anno in formato YYYY"}.\n'
        'Se vuoi annullare, digita Annulla.')
    
    return CONFIRM_DATE_CHOICE

async def confirm_date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for confirming the choice of the date of the rank."""
    date_text = update.message.text
    command = context.user_data.get('command', '')
    selected_date = None

    if '/mese_x' in command:
        # Check if the date has the format mm-YYYY
        if not re.match(r'\d{2}-\d{4}', date_text):
            await update.message.reply_text("Il formato della data deve essere mm-YYYY.", reply_markup=ReplyKeyboardRemove())
            return ERROR_CONVERSATION
        selected_date = f'01-{date_text}'
    elif '/anno_x' in command:
        # Check if the date has the format YYYY
        if not re.match(r'\d{4}', date_text):
            await update.message.reply_text("Il formato della data deve essere YYYY.", reply_markup=ReplyKeyboardRemove())
            return ERROR_CONVERSATION
        # Append '01-01' to make it mm-YYYY format
        selected_date = f'01-01-{date_text}'

    try:
        # Parse the selected date
        selected_date_datetime = datetime.strptime(selected_date, display_format).replace(tzinfo=pytz.timezone('Europe/Rome'))
        # Check if the selected date is in the future
        if selected_date_datetime > datetime.now(pytz.timezone('Europe/Rome')):
            raise ValueError("La data selezionata è nel futuro.")
    except ValueError as e:
        # Handle invalid date format or future date
        await update.message.reply_text(f"{e}", reply_markup=ReplyKeyboardRemove())
        return ERROR_CONVERSATION

    if '/mese_x' in command:
        rank = get_rank(update.message.chat_id, 'month', date_text)
        message = f'Ecco la classifica del mese {date_text}:\n'
        for i, (username, total_count) in enumerate(rank, start=1):
            message += f"{i}. @{username}: {total_count}\n"
        
        generate_table_and_chart(rank, update.message.chat_id, 'month', date_text)

        date_parts = date_text.split('-')
        month = int(date_parts[0])
        year = int(date_parts[1])
        saving_date = str(date_parts[1]) + '_' + str(date_parts[0])

        with open(os.path.join(charts_folder, f'{update.message.chat_id}_{saving_date}.png'), 'rb') as chart:
            await update.message.reply_photo(chart)

        await update.message.reply_text(message)
    if '/anno_x' in command:
        rank = get_rank(update.message.chat_id, 'year', date_text)
        message = f'Ecco la classifica dell\'anno {date_text}:\n'
        for i, (username, total_count) in enumerate(rank, start=1):
            message += f"{i}. @{username}: {total_count}\n"

        generate_table_and_chart(rank, update.message.chat_id, 'year', date_text)

        with open(os.path.join(charts_folder, f'{update.message.chat_id}_{date_text}.png'), 'rb') as chart:
            await update.message.reply_photo(chart)

        await update.message.reply_text(message)

    return ConversationHandler.END

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for ending the conversation."""
    text = update.message.text.lower()
    if 'annulla' in text:
        await update.message.reply_text('Hai annullato il comando.', reply_markup=ReplyKeyboardRemove())

    user_data = context.user_data
    if 'command' in user_data:
        del user_data['command']
    user_data.clear()

    return ConversationHandler.END

async def error_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for errors during the conversation."""
    user_data = context.user_data
    if 'command' in user_data:
        del user_data['command']
    user_data.clear()

    return ConversationHandler.END

async def monthly_rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_mese command, displays monthly ranking."""
    # Get the current month and year
    now = datetime.now(pytz.timezone('Europe/Rome'))
    month = now.strftime("%m")
    year = now.strftime("%Y")

    rank = get_rank(update.message.chat_id, 'month', f'{month}-{year}')
    message = f'Ecco la classifica del mese {f'{month}-{year}'}:\n'
    for i, (username, total_count) in enumerate(rank, start=1):
        message += f"{i}. @{username}: {total_count}\n"

    generate_table_and_chart(rank, update.message.chat_id, 'month', f'{month}-{year}')

    with open(os.path.join(charts_folder, f'{update.message.chat_id}_{year}_{month}.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message)

async def yearly_rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /classifica_anno command, displays yearly ranking."""
    # Get the current month and year
    now = datetime.now(pytz.timezone('Europe/Rome'))
    year = int(now.strftime("%Y"))

    rank = get_rank(update.message.chat_id, 'year', year)
    message = f'Ecco la classifica dell\'anno {year}:\n'
    for i, (username, total_count) in enumerate(rank, start=1):
        message += f"{i}. @{username}: {total_count}\n"

    generate_table_and_chart(rank, update.message.chat_id, 'year', year)

    with open(os.path.join(charts_folder, f'{update.message.chat_id}_{year}.png'), 'rb') as chart:
        await update.message.reply_photo(chart)

    await update.message.reply_text(message)

# Messages handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for processing messages."""
    message_type: str = update.message.chat.type

    # Check if the message contains text and is not empty
    if update.message.text and update.message.text.strip():
        text: str = update.message.text.lower()
        response: str = ''

        if BOT_USERNAME in text:
            response = 'Cosa vuoi dirmi?'

        if '💩' in text:
            username = update.message.from_user.username
            today = datetime.now(pytz.timezone('Europe/Rome')).strftime(storing_format)
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

# Main
if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler('start', start_command))

    manual_addition_handler = ConversationHandler(
        entry_points=[CommandHandler('aggiungi', user_choice)],
        states={
            USER_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               user_choice),
            ],
            DAY_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               day_choice)
            ],
            CONFIRM_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               confirm_choice)
            ],
            ERROR_CONVERSATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               error_conversation)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Annulla$") | filters.Regex("^annulla$"), end_conversation)],
    )
    application.add_handler(manual_addition_handler)

    manual_subtraction_handler = ConversationHandler(
        entry_points=[CommandHandler('togli', user_choice)],
        states={
            USER_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               user_choice),
            ],
            DAY_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               day_choice)
            ],
            CONFIRM_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               confirm_choice)
            ],
            ERROR_CONVERSATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               error_conversation)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Annulla$") | filters.Regex("^annulla$"), end_conversation)],
    )
    application.add_handler(manual_subtraction_handler)

    application.add_handler(CommandHandler('classifica_mese', monthly_rank_command))
    application.add_handler(CommandHandler('classifica_anno', yearly_rank_command))

    monthly_rank_handler = ConversationHandler(
        entry_points=[CommandHandler('mese_x', date_choice)],
        states={
            DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               date_choice),
            ],
            CONFIRM_DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               confirm_date_choice)
            ],
            ERROR_CONVERSATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               error_conversation)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Annulla$") | filters.Regex("^annulla$"), end_conversation)],
    )
    application.add_handler(monthly_rank_handler)

    yearly_rank_handler = ConversationHandler(
        entry_points=[CommandHandler('anno_x', date_choice)],
        states={
            DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               date_choice),
            ],
            CONFIRM_DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               confirm_date_choice)
            ],
            ERROR_CONVERSATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               error_conversation)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Annulla$") | filters.Regex("^annulla$"), end_conversation)],
    )
    application.add_handler(yearly_rank_handler)

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)

    # Polling
    application.run_polling(allowed_updates=filters.Update.MESSAGE)