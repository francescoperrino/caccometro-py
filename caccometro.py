import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import pytz
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

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
USER_CHOICE, DATE_CHOICE, CONFIRM_CHOICE, ERROR_CONVERSATION = range(4)

# Define date formats
storing_format = "%Y-%m-%d"  # Format used for storing dates in the database
display_format = "%d-%m-%Y"  # Format used for displaying dates in messages

# Support functions
def initialize_database(chat_id):
    """Initialize the SQLite database if it doesn't exist."""
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_count
                 (username TEXT,
                 date TEXT,
                 count INTEGER DEFAULT 0,
                 PRIMARY KEY (username, date))''')
    conn.commit()
    conn.close()

def get_count(username, date, chat_id):
    """Get the count of poop emojis for a given user and date."""
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('SELECT count FROM user_count WHERE username = ? AND date = ?', (username, date))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        return 0

def update_count(username, date, count, chat_id):
    """Update the count of poop emojis for a given user and date."""
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_count WHERE username = ? AND date = ?', (username, date))
    if count > 0:
        c.execute('INSERT INTO user_count (username, date, count) VALUES (?, ?, ?)', (username, date, count))
    conn.commit()
    conn.close()

def get_users(chat_id):
    """Get a list of users who have a count of poop emojis greater than zero."""
    users = []
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT username FROM user_count WHERE count > 0')
    rows = c.fetchall()
    conn.close()
    for row in rows:
        users.append(row[0])
    return users

def get_dates(username, chat_id):
    """Get a list of dates for which the specified user has a count of poop emojis greater than zero."""
    dates = []
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('SELECT date FROM user_count WHERE username = ? AND count > 0 ORDER BY date DESC LIMIT 10', (username,))
    rows = c.fetchall()
    dates = [datetime.strptime(row[0], '%Y-%m-%d').strftime('%d-%m-%Y') for row in rows]  # Change date format
    conn.close()
    return dates

def get_rank(chat_id):
    """Get the monthly rank of users based on the count of poop emojis."""
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime(storing_format)
    start_month = today.replace(today[8:11], '01', 1)
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('SELECT username, SUM(count) AS partial_count FROM user_count WHERE date >= ? GROUP BY username ORDER BY partial_count DESC',
              (start_month,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_monthly_stats(username, chat_id):
    """Get the count of poop emojis for the specified user in the current month."""
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime(storing_format)
    start_month = today.replace(today[8:10], '01', 1)
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('SELECT date, count FROM user_count WHERE username = ? AND date >= ?', (username, start_month))
    rows = c.fetchall()
    conn.close()
    monthly_count = sum(count for _, count in rows)
    return monthly_count

def get_yearly_stats(username, chat_id):
    """Get the count of poop emojis for the specified user in the current year."""
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime(storing_format)
    start_year = today.replace(today[5:7], '01', 1).replace(today[8:11], '01', 1)
    conn = sqlite3.connect(str(chat_id) + '_bot_data.db')
    c = conn.cursor()
    c.execute('SELECT date, count FROM user_count WHERE username = ? AND date >= ?', (username, start_year))
    rows = c.fetchall()
    conn.close()
    yearly_count = sum(count for _, count in rows)
    return yearly_count

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

        return DATE_CHOICE

async def date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
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
    """Handler for the /classifica command, displays monthly ranking."""
    rank = get_rank(update.message.chat_id)
    message = f'Ecco la classifica del mese {datetime.now(pytz.timezone("Europe/Rome")).strftime("%m-%Y")}:\n'
    for i, (username, total_count) in enumerate(rank, start=1):
        message += f"{i}. @{username}: {total_count}\n"
    await update.message.reply_text(message)

async def monthly_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /mese command, displays user's monthly poop count."""
    username = update.message.from_user.username
    monthly_count = get_monthly_stats(username, update.message.chat_id)
    await update.message.reply_text(
        f'@{username} questo mese hai fatto 💩 {monthly_count} ' + ('volte' if monthly_count > 1 else 'volta') + '!')

async def yearly_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /anno command, displays user's yearly poop count."""
    username = update.message.from_user.username
    yearly_count = get_yearly_stats(username, update.message.chat_id)
    await update.message.reply_text(
        f'@{username} quest\'anno hai fatto 💩 {yearly_count} ' + ('volte' if yearly_count > 1 else 'volta') + '!')

# Messages handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for processing messages."""
    message_type: str = update.message.chat.type
    text: str = update.message.text.lower()
    response: str = ''

    if not text or text.isspace():
        return

    if BOT_USERNAME in text:
        response = 'Cosa vuoi dirmi?'

    if '💩' in text:
        username = update.message.from_user.username
        today = datetime.now(pytz.timezone('Europe/Rome')).strftime(storing_format)
        count = get_count(username, today, update.message.chat_id)
        update_count(username, today, count + 1, update.message.chat_id)
        response = f'Complimenti @{username}, oggi hai fatto 💩 {count + 1} ' + (
            'volte' if count > 1 else 'volta') + '!'

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
            DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               date_choice)
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
            DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Annulla$") & ~filters.Regex("^annulla$"),
                               date_choice)
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

    application.add_handler(CommandHandler('classifica', monthly_rank_command))
    application.add_handler(CommandHandler('mese', monthly_user_command))
    application.add_handler(CommandHandler('anno', yearly_user_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)

    # Polling
    application.run_polling(allowed_updates=filters.Update.MESSAGE)