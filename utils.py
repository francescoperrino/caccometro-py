import os
import calendar
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from database import get_count, DISPLAY_FORMAT, CHARTS_FOLDER
import locale
from math import ceil
from datetime import datetime, timedelta
from collections import defaultdict

# Set the locale to Italian
locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')

# Check if charts folder exists, if not, create it
os.makedirs(CHARTS_FOLDER, exist_ok=True)

def generate_table_and_chart(rank, chat_id, time_period, date):
    """
    Generates the monthly ranking table and chart.

    Args:
        rank (list): List of tuples containing username and count.
        chat_id (int): ID of the chat.
        time_period (str): Time period ('month' or 'year').
        date (str): Date in 'month-year' or 'year' format.

    Returns:
        None
    """
    if time_period == 'month':
        # Parse the input date for monthly rank (format: month-year)
        date_parts = date.split('-')
        month = int(date_parts[0])
        year = int(date_parts[1])
        _, days = calendar.monthrange(year, month)
        period_label = calendar.month_name[month] + ' ' + str(year)
        saving_date = str(date_parts[1]) + '_' + str(date_parts[0])
        steps = days
        x_labels = [str(day) for day in range(1, days + 1)]  # Labels for each day of the month
    elif time_period == 'year':
        # Parse the input date for yearly rank (format: year)
        year = int(date)
        days = 365 if calendar.isleap(year) else 366  # Number of days in a year
        steps = 12  # Number of months in a year
        period_label = str(year)
        saving_date = date
        x_labels = [calendar.month_abbr[count_month] for count_month in range(1, steps + 1)]  # Labels for each month of the year

    # Create the figure with the desired dimensions
    fig = plt.figure(figsize=(15, 10))
    axes = fig.subplots(2, 1)

    # Generate the table
    users = [user for user, _ in rank]
    # Sort users alphabetically
    users = sorted(users)
    axes[1].set_xticklabels([])
    if time_period == 'month':
        table_data = [[''] + [f'{step}' for step in range(1, steps + 1)] + ['Total']]  # Set days when time_period is 'month'
    elif time_period == 'year':
        table_data = [[''] + [f'{calendar.month_abbr[count_month]}' for count_month in range(1, steps + 1)] + ['Total']]  # Set months when time_period is 'year'

    max_total = 0  # Variable to store the maximum total count for highlighting

    for user in users:
        row = [user]
        total_count = 0
        for step in range(1, steps + 1):
            if time_period == 'month':
                count_date = f'{year}-{month:02}-{step:02}'
            elif time_period == 'year':
                count_date = f'{year}-{step:02}'
            count = get_count(user, count_date, chat_id)  # Get the count for the specific day or month
            total_count += count
            row.append(count)
        row.append(total_count)  # Add total count for the period
        table_data.append(row)

        # Update max_total if necessary
        max_total = max(max_total, total_count)

    # Draw the table
    table = axes[0].table(cellText=table_data, loc='center', colWidths=[0.1] + [0.03] * steps + [0.05],  
                          cellLoc='center', fontsize=8)

    for key, cell in table.get_celld().items():
        cell.set_edgecolor('black')  # Set edge color for each cell
        cell.set_linewidth(1)  # Set linewidth for each cell

    table.auto_set_font_size(True)
    table.set_fontsize(8)

    # Set title for the table (month name and year)
    axes[0].set_title(f'{period_label.capitalize()}', fontsize=14)

    # Hide the axes for the table
    axes[0].axis('off')

    # Highlight cell with highest total count in brown color
    for i, row in enumerate(table_data):
        for j, value in enumerate(row):
            if value == max_total and j == len(row) - 1:  # Check if it's the last cell (total column)
                table.get_celld()[(i, j)].set_facecolor('#D2B48C')  # Set brown color for total column

    # Generate the chart
    for user in users:
        cumulative_counts = []
        cumulative_count = 0
        for day in range(1, days + 1):
            if time_period == 'month':
                count_date = f'{year}-{month:02}-{day:02}'
            elif time_period == 'year':
                doy = datetime.strptime(f'{year}-{day}', '%Y-%j')
                count_date = doy.strftime('%Y-%m-%d')
            count = get_count(user, count_date, chat_id)  # Get the count for each day in month or year
            cumulative_count += count
            cumulative_counts.append(cumulative_count)

        axes[1].plot(range(1, days + 1), cumulative_counts, label=user)

    # Set legend for the chart below the chart
    axes[1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=len(users), fontsize=8)

    # Set labels on x-axis
    if time_period == 'month':
        axes[1].set_xticks(range(1, days + 1))
        axes[1].set_xticklabels(x_labels)  # Set x-axis labels based on time_period
    elif time_period == 'year':
        # Find the start day of each month in the year
        start_days = [1]  # Start with the first day of January
        for month in range(1, 12):  # Loop through the months
            _, days_in_month = calendar.monthrange(year, month)
            start_days.append(start_days[-1] + days_in_month)  # Add the start day of the next month
        # Set the ticks at the start of each month
        axes[1].set_xticks(start_days)
        axes[1].set_xticklabels(x_labels)  # Set x-axis labels based on time_period

    # Set y-axis range from 0 to the next multiple of 10 after max_total
    max_y = ceil((max_total + 1) / 10) * 10
    axes[1].set_ylim(bottom=0, top=max_y)

    # Set y-axis ticks every 10
    axes[1].set_yticks(range(0, max_y + 10, 10))

    # Add horizontal lines every count
    for count in range(0, max_y + 1, 1):
        axes[1].axhline(y=count, color='#DDDDDD', linestyle='--', linewidth=0.3)
    
    # Add horizontal lines every 5 count
    for count in range(5, max_y + 5, 5):
        axes[1].axhline(y=count, color='#CCCCCC', linestyle='--', linewidth=0.7)
    
    # Add horizontal lines every 10 count
    for count in range(10, max_y + 10, 10):
        axes[1].axhline(y=count, color='#888888', linestyle='--', linewidth=1)

    # Add vertical lines
    if time_period == 'month':
        for day in range(1, days + 1):
            axes[1].axvline(x=day, color='#DDDDDD', linestyle='--', linewidth=0.3)
    elif time_period == 'year':
        # Find the start day of each month in the year and add vertical lines at those points
        start_days = [1]  # Start with the first day of January
        for month in range(1, 12):  # Loop through the months
            _, days_in_month = calendar.monthrange(year, month)
            start_days.append(start_days[-1] + days_in_month)  # Add the start day of the next month
        for start_day in start_days:
            axes[1].axvline(x=start_day, color='#DDDDDD', linestyle='--', linewidth=0.3)

    # Set x-axis limits to include only the actual days of the month
    axes[1].set_xlim(left=1, right=days)
    
    # Save the figure to an image file
    plt.savefig(os.path.join(CHARTS_FOLDER, f'{chat_id}_{saving_date}.png'), bbox_inches='tight')

    # Close figure
    plt.close(fig)

def analyze_user_record(rows):
    """
    Analyzes user activity records to extract key statistics, including longest streaks, 
    maximum and minimum occurrences, and longest gap periods.

    Args:
        rows (list of tuples): A list of (date, count) tuples, where:
            - date (str): The date in 'YYYY-MM-DD' format.
            - count (int): The recorded count for that date.

    Returns:
        dict: A dictionary containing:
            - 'max_daily_count' (int): The highest count recorded in a single day.
            - 'max_days' (list): A list of dates (%d-%m-%Y) with the highest count.
            - 'max_monthly_count' (int): The highest total count recorded in a month.
            - 'max_months' (list): A list of months (%m-%Y) with the highest count.
            - 'min_monthly_count' (int): The lowest total count recorded in a month.
            - 'min_months' (list): A list of months (%m-%Y) with the lowest count.
            - 'max_streak_days' (int): The longest consecutive streak of recorded occurrences.
            - 'max_streak_period' (tuple or None): The start and end dates (%d-%m-%Y) of the longest streak, 
            or None if no streak exists.
            - 'max_streak_count' (int): The highest total occurrences over a consecutive streak.
            - 'max_streak_count_period' (tuple or None): The start and end dates (%d-%m-%Y) of this occurrence streak, 
            or None if no such streak exists.
            - 'max_gap_days' (int): The longest period without recorded occurrences.
            - 'max_gap_period' (tuple or None): The start and end dates (%d-%m-%Y) of the longest gap period, 
            or None if no gap exists.
    """
    # Convert records into a dictionary
    records = {datetime.strptime(date, "%Y-%m-%d"): count for date, count in rows}
    
    # Finding daily max counts
    max_daily_count = max(records.values())
    max_days = [date.strftime(DISPLAY_FORMAT) for date, count in records.items() if count == max_daily_count]
    
    # Find monthly max and min counts
    monthly_counts = defaultdict(int)
    for date, count in records.items():
        monthly_counts[(date.year, date.month)] += count

    now = datetime.now()
    current_month = (now.year, now.month)

    # Finding the max and min monthly counts excluding the current month
    max_monthly_count = max((count for (year, month), count in monthly_counts.items() if (year, month) != current_month), default=None)
    min_monthly_count = min((count for (year, month), count in monthly_counts.items() if (year, month) != current_month), default=None)

    # Retrieving months with max and min counts
    max_months = [f"{month:02d}-{year}" for (year, month), count in monthly_counts.items() if count == max_monthly_count]
    min_months = [f"{month:02d}-{year}" for (year, month), count in monthly_counts.items() if count == min_monthly_count]

    # Calculate the date range from the first to the last occurrence date
    sorted_dates = sorted(records.keys())
    start_date = sorted_dates[0]
    end_date = sorted_dates[-1]

    # Generate all dates within the range
    all_dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    max_streak_days = 0  # Longest sequence of consecutive days with occurrences
    max_streak_count = 0  # Highest sum of occurrences in a consecutive sequence
    max_gap_days = 0  # Longest sequence of consecutive days without occurrences
    
    current_streak = 0
    current_streak_count = 0
    max_streak_start = max_streak_end = None
    
    max_count_streak_start = max_count_streak_end = None
    
    current_gap = 0
    max_gap_start = max_gap_end = None
    
    for date in all_dates:
        count = records.get(date, 0)
        
        if count > 0:
            # Streak tracking
            if current_streak == 0:
                streak_start = date
            current_streak += 1
            current_streak_count += count
            
            # If this is the longest streak, update
            if current_streak > max_streak_days:
                max_streak_days = current_streak
                max_streak_start, max_streak_end = streak_start, date
            
            # Tracking max count streak
            if current_streak_count > max_streak_count:
                max_streak_count = current_streak_count
                max_count_streak_start, max_count_streak_end = streak_start, date
            
            current_gap = 0  # Reset gap tracking
        else:
            # Gap tracking
            if current_gap == 0:
                gap_start = date
            current_gap += 1
            
            # If this is the longest gap, update
            if current_gap > max_gap_days:
                max_gap_days = current_gap
                max_gap_start, max_gap_end = gap_start, date
            
            # Reset streak tracking
            current_streak = 0
            current_streak_count = 0

    return {
        "max_daily_count": max_daily_count,
        "max_days": max_days,
        "max_monthly_count": max_monthly_count,
        "max_months": max_months,
        "min_monthly_count": min_monthly_count,
        "min_months": min_months,
        "max_streak_days": max_streak_days,
        "max_streak_period": (max_streak_start.strftime(DISPLAY_FORMAT), max_streak_end.strftime(DISPLAY_FORMAT)) if max_streak_start else None,
        "max_streak_count": max_streak_count,
        "max_streak_count_period": (max_count_streak_start.strftime(DISPLAY_FORMAT), max_count_streak_end.strftime(DISPLAY_FORMAT)) if max_count_streak_start else None,
        "max_gap_days": max_gap_days,
        "max_gap_period": (max_gap_start.strftime(DISPLAY_FORMAT), max_gap_end.strftime(DISPLAY_FORMAT)) if max_gap_start else None,
    }