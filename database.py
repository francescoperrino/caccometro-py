import os
import sqlite3
from datetime import datetime
import pytz
import calendar

# Define date formats
storing_format = "%Y-%m-%d"  # Format used for storing dates in the database
display_format = "%d-%m-%Y"  # Format used for displaying dates in messages

# Folder to store databases
db_folder = 'db'

# Function to initialize the database
def initialize_database(chat_id):
    """Initialize the SQLite database if it doesn't exist."""
    # Check if the database folder exists, if not, create it
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
    # Connect to the database file, creating it if it doesn't exist
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Create the user_count table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS user_count
                 (username TEXT,
                 date TEXT,
                 count INTEGER DEFAULT 0,
                 PRIMARY KEY (username, date))''')
    conn.commit()
    conn.close()

# Function to get the count of poop emojis for a given user and date
def get_count(username, date, chat_id):
    """Get the count of poop emojis for a given user and date."""
    # Connect to the database
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    
    # Determine if the input date is a day or a month
    try:
        parsed_date = datetime.strptime(date, '%Y-%m-%d')
        start_date = parsed_date.strftime('%Y-%m-%d')
        end_date = parsed_date.strftime('%Y-%m-%d')
    except ValueError:
        try:
            parsed_date = datetime.strptime(date, '%Y-%m')
            year = parsed_date.year
            month = parsed_date.month
            _, days_in_month = calendar.monthrange(year, month)
            start_date = parsed_date.strftime('%Y-%m-01')
            end_date = parsed_date.strftime(f'%Y-%m-{days_in_month}')
        except ValueError:
            conn.close()
            return 0
    
    # Execute SQL query to retrieve the count for the specified user and date or month
    c.execute('SELECT SUM(count) FROM user_count WHERE username = ? AND date BETWEEN ? AND ?', (username, start_date, end_date))
    row = c.fetchone()
    conn.close()
    
    # Return the count if found, otherwise return 0
    if row[0] is not None:
        return row[0]
    else:
        return 0

# Function to update the count of poop emojis for a given user and date
def update_count(username, date, count, chat_id):
    """Update the count of poop emojis for a given user and date."""
    # Connect to the database
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Delete existing count for the specified user and date
    c.execute('DELETE FROM user_count WHERE username = ? AND date = ?', (username, date))
    # If the count is greater than 0, insert the new count
    if count > 0:
        c.execute('INSERT INTO user_count (username, date, count) VALUES (?, ?, ?)', (username, date, count))
    conn.commit()
    conn.close()

# Function to get a list of users who have a count of poop emojis greater than zero
def get_users(chat_id):
    """Get a list of users who have a count of poop emojis greater than zero."""
    users = []
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
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
    # Connect to the database
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Execute SQL query to retrieve dates with count > 0 for the specified user
    c.execute('SELECT date FROM user_count WHERE username = ? AND count > 0 ORDER BY date DESC LIMIT 10', (username))
    rows = c.fetchall()
    conn.close()
    # Format dates and return them
    dates = [datetime.strptime(row[0], '%Y-%m-%d').strftime('%d-%m-%Y') for row in rows]
    return dates

# Function to get the rank of users based on the count of poop emojis
def get_rank(chat_id, time_period, date):
    """Get the rank of users based on the count of poop emojis for the specified time period."""
    if time_period == 'month':
        # Parse the input date for monthly rank (format: month-year)
        date_parts = date.split('-')
        month_str = date_parts[0].zfill(2)  # Aggiungi uno zero iniziale, se necessario
        year_str = date_parts[1]
        start_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y').strftime(storing_format)
        # Get the end of the month
        end_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y')\
                        .replace(day=calendar.monthrange(int(year_str), int(month_str))[1])\
                        .strftime(storing_format)
    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        start_period = datetime.strptime(f'01-01-{date}', '%d-%m-%Y').strftime(storing_format)
        end_period = datetime.strptime(f'31-12-{date}', '%d-%m-%Y').strftime(storing_format)
    else:
        raise ValueError("Invalid time_period. It should be 'month' or 'year'.")

    # Connect to the database
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
    c = conn.cursor()

    # Execute SQL query to get the rank based on the time_period
    c.execute('''SELECT username, SUM(count) AS partial_count
              FROM user_count
              WHERE date BETWEEN ? AND ?
              GROUP BY username
              ORDER BY partial_count DESC''', (start_period, end_period))
    
    rows = c.fetchall()
    conn.close()
    return rows

# Function to get the count of poop emojis for the specified user in the current month
def get_monthly_stats(username, chat_id):
    """Get the count of poop emojis for the specified user in the current month."""
    # Get the current date in storing_format
    today = datetime.now(pytz.timezone('Europe/Rome')).strftime(storing_format)
    start_month = today.replace(today[8:10], '01', 1)  # Set the start of the month
    # Connect to the database
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Execute SQL query to get the count for the specified user in the current month
    c.execute('SELECT date, count FROM user_count WHERE username = ? AND date >= ?', (username, start_month))
    rows = c.fetchall()
    conn.close()
    # Calculate and return the monthly count
    monthly_count = sum(count for _, count in rows)
    return monthly_count

# Function to get the count of poop emojis for the specified user in the current year
def get_yearly_stats(username, chat_id):
    """Get the count of poop emojis for the specified user in the current year."""
    # Get today's date
    today = datetime.now(pytz.timezone('Europe/Rome'))

    # Set the first day of the current year
    start_year = today.replace(month=1, day=1)

    # Format the date in the desired format
    start_year = start_year.strftime(storing_format)
    
    # Connect to the database
    conn = sqlite3.connect(os.path.join(db_folder, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Execute SQL query to get the count for the specified user in the current year
    c.execute('SELECT date, count FROM user_count WHERE username = ? AND date >= ?', (username, start_year))
    rows = c.fetchall()
    conn.close()
    # Calculate and return the yearly count
    yearly_count = sum(count for _, count in rows)
    return yearly_count