import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import pytz
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

    if not isdate or  context.user_data['selected_date'] > datetime.now(pytz.timezone('Europe/Rome')).strftime("%d-%m-%Y"):
        await update.message.reply_text("Hai inserito una scelta non valida, comando annullato!", reply_markup = ReplyKeyboardRemove())
        return ERROR_CONVERSATION
    else:
        await update.message.reply_text(f"Hai scelto @{context.user_data['selected_user'].lower()} e il giorno {context.user_data['selected_date']}.", reply_markup = ReplyKeyboardRemove())
        
        if context.user_data['command'] == '/aggiungi':
            user_poop_count[context.user_data['selected_user']][context.user_data['selected_date']] += 1
        elif context.user_data['command'] == '/togli':
            user_poop_count[context.user_data['selected_user']][context.user_data['selected_date']] -= 1
        
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

async def monthly_rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime("%d-%m-%Y")
    start_month = today.replace(today[0:2], '01', 1)
    
    await update.message.reply_text(f'Ecco la classifica del mese {datetime.now(pytz.timezone('Europe/Rome')).strftime('%m-%Y')}:')
    
    users = get_users()
    rank = {}
    
    for user in users:
        rank.setdefault(user, {}).setdefault(today, 0)
        for user in user_poop_count:
            for date in user_poop_count[user]:
                if date >= start_month and date <= today:
                    rank[user][today] += user_poop_count[user][date]
    
    rank = dict(rank.items(), key = lambda item: item[1])
    for ii in range(1, len(rank)):
        await update.message.reply_text(f'{ii}. @{[*rank][0]}: {rank[user][today]}')
    
    await update.message.reply_text(f'Complimenti a @{[*rank][0]} che questo mese ci stai dando alla grande.')

    return rank

async def monthly_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime("%d-%m-%Y")
    start_month = today.replace(today[0:2], '01', 1)
    monthly = 0
    
    for date in user_poop_count[user.username]:
        if date >= start_month and date <= today:
            monthly += user_poop_count[user.username][date]
    
    await update.message.reply_text(f'{user.name} questo mese hai 💩 {monthly} ' + ('volte' if monthly > 1 else 'volta') + '!')

    return monthly

async def yearly_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime("%d-%m-%Y")
    start_year = today.replace(today[0:2], '01', 1).replace(today[3:5], '01', 1)
    yearly = 0
    
    for date in user_poop_count[user.username]:
        if date >= start_year and date <= today:
            yearly += user_poop_count[user.username][date]
    
    await update.message.reply_text(f'{user.name} quest\'anno hai 💩 {yearly} ' + ('volte' if yearly > 1 else 'volta') + '!')

    return yearly

# Messages handlers
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text.lower()
    response: str = ''

    if BOT_USERNAME in text:
        response = 'Cosa vuoi dirmi?'
    
    if '💩' in text:
        user = update.message.from_user
        today = datetime.now(pytz.timezone('Europe/Rome')).strftime("%d-%m-%Y")
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

    application.add_handler(CommandHandler('classifica', monthly_rank_command))
    application.add_handler(CommandHandler('mese', monthly_user_command))
    application.add_handler(CommandHandler('anno', yearly_user_command))

    # Messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    application.add_error_handler(error)

    # Polling
    application.run_polling(allowed_updates = Update.ALL_TYPES)