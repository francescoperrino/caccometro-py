import os
from datetime import datetime
import pytz
import calendar
import matplotlib.pyplot as plt
from database import get_count

# Define date formats
storing_format = "%Y-%m-%d"  # Format used for storing dates in the database
display_format = "%d-%m-%Y"  # Format used for displaying dates in messages

# Folder to store charts
charts_folder = 'charts'

# Check if charts folder exists, if not, create it
if not os.path.exists(charts_folder):
    os.makedirs(charts_folder)

def generate_table_and_chart(rank, chat_id):
    """Generates the monthly ranking table and chart."""
    # Get the current month and year
    now = datetime.now(pytz.timezone('Europe/Rome'))
    month = now.month
    year = now.year

    # Calculate the number of days in the current month
    _, days_in_month = calendar.monthrange(year, month)

    # Create subplots for the table and the chart
    fig, axes = plt.subplots(2, 1, figsize=(12, 12))

    # Generate the table
    users = [user for user, _ in rank]
    table_data = [[''] + [f'{day}' for day in range(1, days_in_month + 1)] + ['Total']]

    max_total = 0  # Variable to store the maximum total count for highlighting

    for user in users:
        row = [user]
        total_count = 0
        for day in range(1, days_in_month + 1):
            count = get_count(user, f'{year}-{month:02}-{day:02}', chat_id)  # Get the count for the specific day
            total_count += count
            row.append(count)
        row.append(total_count)  # Add total count for the month
        table_data.append(row)

        # Update max_total if necessary
        max_total = max(max_total, total_count)

    # Draw the table
    table = axes[0].table(cellText=table_data, loc='center', colWidths=[0.1] + [0.03] * days_in_month + [0.05],  
                          cellLoc='center', fontsize=8)

    for key, cell in table.get_celld().items():
        cell.set_edgecolor('black')  # Set edge color for each cell
        cell.set_linewidth(1.2)  # Set linewidth for each cell

    table.auto_set_font_size(True)
    table.set_fontsize(8)

    # Set title for the table (month name and year)
    axes[0].set_title(f'{calendar.month_name[month]} {year}', fontsize=14, pad=20)

    # Hide the axes for the table
    axes[0].axis('off')

    # Highlight cell with highest total count in brown color
    for i, row in enumerate(table_data):
        for j, value in enumerate(row):
            if value == max_total and j != 0:  # Exclude username column
                table.get_celld()[(i, j)].set_facecolor('#D2B48C')  # Set brown color

    # Generate the chart
    for user in users:
        cumulative_counts = []
        cumulative_count = 0
        for day in range(1, days_in_month + 1):
            count = get_count(user, f'{year}-{month:02}-{day:02}', chat_id)  # Get the count for the specific day
            cumulative_count += count
            cumulative_counts.append(cumulative_count)

        axes[1].plot(range(1, days_in_month + 1), cumulative_counts, label=user)

    # Set legend for the chart below the chart
    axes[1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=len(users), fontsize=10)  # Set legend below the chart

    # Adjust space between subplots
    plt.subplots_adjust(hspace=0)  # Reduce the space between the table and the chart

    # Set labels on x-axis for the days of the month
    axes[1].set_xticks(range(1, days_in_month + 1))
    axes[1].set_xticklabels([f'{day}' for day in range(1, days_in_month + 1)])

    # Set y-axis range from 0 and ticks every 10
    axes[1].set_ylim(bottom=0)
    axes[1].set_yticks(range(0, max(cumulative_counts) + 10, 10))  # Adjust y-ticks to include space for the count label

    # Add horizontal lines every 5 count
    for count in range(5, max(cumulative_counts) + 5, 5):
        axes[1].axhline(y=count, color='#CCCCCC', linestyle='--', linewidth=0.5)
    # Add horizontal lines every 10 count
    for count in range(10, max(cumulative_counts) + 10, 10):
        axes[1].axhline(y=count, color='#888888', linestyle='--', linewidth=1)

    plt.savefig(os.path.join(charts_folder, f'{chat_id}_monthly_chart.png'), bbox_inches='tight')  # Save the figure to an image file