import os
import calendar
import matplotlib.pyplot as plt
from database import get_count
import locale
from math import ceil
from datetime import datetime

# Define date formats
storing_format = "%Y-%m-%d"  # Format used for storing dates in the database
display_format = "%d-%m-%Y"  # Format used for displaying dates in messages

# Folder to store charts
charts_folder = 'charts'

# Set the locale to Italian
locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')

# Check if charts folder exists, if not, create it
if not os.path.exists(charts_folder):
    os.makedirs(charts_folder)

def generate_table_and_chart(rank, chat_id, time_period, date):
    """Generates the monthly ranking table and chart."""
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
    plt.savefig(os.path.join(charts_folder, f'{chat_id}_{saving_date}.png'), bbox_inches='tight')

    # Close figure
    plt.close(fig)