import os
import sqlite3
from datetime import datetime
import numpy as np
import calendar

# Define date formats
STORING_FORMAT = "%Y-%m-%d"  # Format used for storing dates in the database

# Folder to store databases
DB_FOLDER = 'db'

# Function to initialize the database
def initialize_database(chat_id):
    """Initialize the SQLite database if it doesn't exist."""
    # Check if the database folder exists, if not, create it
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
    # Connect to the database file, creating it if it doesn't exist
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
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
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    
    # Determine if the input date is a day, a month, or invalid
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
            try:
                parsed_date = datetime.strptime(date, '%d-%m-%Y')
                start_date = parsed_date.strftime('%Y-%m-%d')
                end_date = parsed_date.strftime('%Y-%m-%d')
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
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
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
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
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
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()
    # Execute SQL query to retrieve dates with count > 0 for the specified user
    c.execute('SELECT date FROM user_count WHERE username = ? AND count > 0 ORDER BY date DESC LIMIT 10', (username,))
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
        month_str = date_parts[0].zfill(2)  # Add leading zero, if necessary
        year_str = date_parts[1]
        start_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y').strftime(STORING_FORMAT)
        # Get the end of the month
        end_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y')\
                        .replace(day=calendar.monthrange(int(year_str), int(month_str))[1])\
                        .strftime(STORING_FORMAT)
    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        start_period = datetime.strptime(f'01-01-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
        end_period = datetime.strptime(f'31-12-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
    else:
        raise ValueError("Invalid time_period. It should be 'month' or 'year'.")

    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
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

# Function to get the stats of users based on the count of poop emojis
def get_statistics(chat_id, time_period, date):
    """Get the statistics of users based on the count of poop emojis for the specified time period."""
    current_month = datetime.now().month
    current_year = datetime.now().year
    if time_period == 'month':
        # Parse the input date for monthly rank (format: month-year)
        date_parts = date.split('-')
        month_str = date_parts[0].zfill(2)  # Add leading zero, if necessary
        year_str = date_parts[1]
        start_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y').strftime(STORING_FORMAT)
        # Get the end of the month
        end_period = datetime.strptime(f'{month_str}-{year_str}', '%m-%Y')\
                        .replace(day=calendar.monthrange(int(year_str), int(month_str))[1])\
                        .strftime(STORING_FORMAT)
        month = int(date_parts[0])
        year = int(date_parts[1])
        _, days = calendar.monthrange(year, month)  # Number of days in the month
        current_days = datetime.now().day
    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        start_period = datetime.strptime(f'01-01-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
        end_period = datetime.strptime(f'31-12-{date}', '%d-%m-%Y').strftime(STORING_FORMAT)
        year = int(date)
        days = 365 if calendar.isleap(int(date)) else 366  # Number of days in a year
        current_days = (datetime.now() - datetime(current_year, 1, 1)).days + 1
    else:
        raise ValueError("Invalid time_period. It should be 'month' or 'year'.")

    # Connect to the database
    conn = sqlite3.connect(os.path.join(DB_FOLDER, f'{chat_id}_bot_data.db'))
    c = conn.cursor()

    # Execute SQL query to get the counts for each user in the specified period
    c.execute('''SELECT username, count
              FROM user_count
              WHERE date BETWEEN ? AND ?
              ORDER BY username''', (start_period, end_period))

    rows = c.fetchall()
    conn.close()

    # Organize the counts into dictionaries for each user
    user_counts = {}
    for username, count in rows:
        if username not in user_counts:
            user_counts[username] = []
        user_counts[username].append(count)

    # Calculate mean and variance for each user
    user_statistics = []
    for username, counts in user_counts.items():
        # Calculate mean and variance based on days in the month or year
        if time_period == 'month' and year == current_year and month == current_month:
            mean = round(sum(counts) / current_days, 2)
            variance = round(sum((x - mean) ** 2 for x in counts) / current_days, 2)
        elif time_period == 'year' and year == current_year:
            mean = round(sum(counts) / current_days, 2)
            variance = round(sum((x - mean) ** 2 for x in counts) / current_days, 2)
        else:
            mean = round(sum(counts) / days, 2)
            variance = round(sum((x - mean) ** 2 for x in counts) / days, 2)
        user_statistics.append({'username': username, 'mean': mean, 'variance': variance})

    # Sort user_statistics by mean and variance in descending order
    sorted_user_statistics = sorted(user_statistics, key=lambda x: (x['mean'], x['variance']), reverse=True)

    return sorted_user_statistics