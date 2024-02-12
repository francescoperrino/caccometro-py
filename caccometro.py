import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Enable logging
logging.basicConfig(
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Load bot info from .env
load_dotenv()
BOT_USERNAME = os.environ.get('BOT_USERNAME')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

USER_CHOICE, DATE_CHOICE, CONFIRM_CHOICE, ERROR_CONVERSATION = range(4)
user_poop_count = {}

# Support functions
def get_users() -> list:
    users = []
    for name in user_poop_count:
        if name not in users:
            users.append(name)
    return users

def get_date(selected_user) -> list:
    dates = []
    for date in user_poop_count.get(selected_user):
            dates.append(date)
    dates.sort(key = lambda date: datetime.strptime(date, "%d-%m-%Y"), reverse = True)
    if len(date)>= 10:
        del dates[10:]
    return dates

def manual_addition(selected_user, selected_dates):
    user_poop_count[selected_user][selected_dates] += 1

def manual_subtraction(selected_user, selected_dates):
    user_poop_count[selected_user][selected_dates] -= 1

# Commands handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Ciao, sono Caccometro. Manda 💩 quando hai fatto il tuo dovere.')

async def user_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = update.message.text
    context.user_data['command'] = text
    await update.message.reply_text('Hai scelto di ' + ('incrementare' if context.user_data['command'] == '/aggiungi' else 'ridurre') + ' il conteggio di 💩 a un utente.')
    await update.message.reply_text('Se vuoi annullare, digita Annulla.')

    users = get_users()
    reply_keyboard = []
    reply_keyboard.append(users)
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text('Chi scegli?', reply_markup = markup)

    return DATE_CHOICE

async def date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text = update.message.text
    context.user_data['selected_user'] = text
    
    if context.user_data['selected_user'] not in get_users():
        await update.message.reply_text("Hai inserito una scelta non valida, comando annullato!", reply_markup = ReplyKeyboardRemove())
        return ERROR_CONVERSATION
    else:
        await update.message.reply_text(f"Hai scelto @{context.user_data['selected_user'].lower()}!", reply_markup = ReplyKeyboardRemove())
        
        if context.user_data['command'] == '/aggiungi':
            await update.message.reply_text('Ora inserisci il giorno (in formato dd-mm-yyyy):')
        elif context.user_data['command'] == '/togli':
            dates = []
            dates = get_date(context.user_data['selected_user'])
            reply_keyboard = []
            reply_keyboard.append(dates)
            markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
            await update.message.reply_text('Ora scegli il giorno:', reply_markup = markup)

        return CONFIRM_CHOICE

async def confirm_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data['selected_date'] = text

    try:
        isdate = bool(datetime.strptime(context.user_data['selected_date'], "%d-%m-%Y"))
    except ValueError:
        isdate = False

    if not isdate or  context.user_data['selected_date'] > datetime.today().strftime("%d-%m-%Y"):
        await update.message.reply_text("Hai inserito una scelta non valida, comando annullato!", reply_markup = ReplyKeyboardRemove())
        return ERROR_CONVERSATION
    else:
        await update.message.reply_text(f"Hai scelto @{context.user_data['selected_user'].lower()} e il giorno {context.user_data['selected_date']}.", reply_markup = ReplyKeyboardRemove())
        
        if context.user_data['command'] == '/aggiungi':
            manual_addition(context.user_data['selected_user'], context.user_data['selected_date'])
        elif context.user_data['command'] == '/togli':
            manual_subtraction((context.user_data['selected_user'], context.user_data['selected_date']))
        
        await update.message.reply_text(f"Il conteggio di @{context.user_data['selected_user'].lower()} nel giorno {context.user_data['selected_date']} è stato aggiornato a {user_poop_count[context.user_data['selected_user']][context.user_data['selected_date']]} 💩.", reply_markup = ReplyKeyboardRemove())
        
    return ConversationHandler.END

async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.lower()
    if text == 'annulla':
        await update.message.reply_text('Hai annullato il comando.', reply_markup = ReplyKeyboardRemove())
    
    user_data = context.user_data

    if 'command' in user_data:
        del user_data['command']

    if 'selected_user' in user_data:
        del user_data['selected_user']
    
    if 'selected_date' in user_data:
        del user_data['selected_date']
    
    user_data.clear()
    return ConversationHandler.END

async def error_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data

    if 'command' in user_data:
        del user_data['command']

    if 'selected_user' in user_data:
        del user_data['selected_user']
    
    if 'selected_date' in user_data:
        del user_data['selected_date']
    
    user_data.clear()

    return ConversationHandler.END

async def monthly_table_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Funzione presto in arrivo.')

async def montly_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Funzione presto in arrivo.')

async def yearly_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Funzione presto in arrivo.')

# Messages handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text.lower()
    response: str = ''

    if BOT_USERNAME in text:
        response = 'Cosa vuoi dirmi?'
    
    if '💩' in text:
        user = update.message.from_user
        today = datetime.today().strftime("%d-%m-%Y")
        user_poop_count.setdefault(user.username, {}).setdefault(today, 0)
        user_poop_count[user.username][today] += 1
        response = f'Bravo {user.name}, oggi hai 💩 {user_poop_count[user.username][today]} ' + ('volte' if user_poop_count[user.username][today] > 1 else 'volta') + '!'
    
    await update.message.reply_text(response)

# Error
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Errore: {context.error}')

# Main
if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler('start', start_command))

    manual_addition_handler = ConversationHandler(
        entry_points = [CommandHandler('aggiungi', user_choice)],
        states = {
            USER_CHOICE: [
                MessageHandler(user_poop_count, user_choice),
            ],
            DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Annulla$") | filters.Regex("^annulla$")), date_choice)
            ],
            CONFIRM_CHOICE: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Annulla$")) | filters.Regex("^annulla$"),confirm_choice)
            ],
            ERROR_CONVERSATION: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Annulla$")) | filters.Regex("^annulla$"),error_conversation),
            ]
        },
        fallbacks = [MessageHandler(filters.Regex("^Annulla$") | filters.Regex("^annulla$"), end_conversation)],
    )
    application.add_handler(manual_addition_handler)

    manual_subtraction_handler = ConversationHandler(
        entry_points = [CommandHandler('togli', user_choice)],
        states = {
            USER_CHOICE: [
                MessageHandler(user_poop_count, user_choice),
            ],
            DATE_CHOICE: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Annulla$") | filters.Regex("^annulla$")), date_choice)
            ],
            CONFIRM_CHOICE: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Annulla$")) | filters.Regex("^annulla$"),confirm_choice)
            ],
            ERROR_CONVERSATION: [
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^Annulla$")) | filters.Regex("^annulla$"),error_conversation),
            ]
        },
        fallbacks = [MessageHandler(filters.Regex("^Annulla$") | filters.Regex("^annulla$"), end_conversation)],
    )
    application.add_handler(manual_subtraction_handler)

    application.add_handler(CommandHandler('classifica', monthly_table_command))
    application.add_handler(CommandHandler('mese', montly_user_command))
    application.add_handler(CommandHandler('anno', yearly_user_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)

    # Polling
    application.run_polling(allowed_updates = Update.ALL_TYPES)