import json
from datetime import datetime, timedelta

def send_response(status_code, message, e = ''):
    if e == '':
        sep = ''
    else:
        sep = '\n'

    response = {
        'status_code': status_code,
        'body': json.dumps({'message': f'{message}{sep}{e}'})
    }

    print(response)
    return response

def parse_query_result(query_result):
    rows = []
    for row in query_result:
        row_data = {}
        for key, value in row.items():
            # Convert any special types if needed (e.g., datetime)
            row_data[key] = value
        rows.append(row_data)
    return rows

def fill_missing_hours(data):
    # Convert data to dictionary for easy lookup
    data_dict = {(entry['date_played_at'], entry['hour_played_at']): entry['f0_'] for entry in data}
    
    # Get the minimum and maximum dates from the data
    min_date = min(entry['date_played_at'] for entry in data)
    max_date = max(entry['date_played_at'] for entry in data)
    
    # Generate all date-hour combinations for the last 24 hours
    date_hour_combinations = []
    current_date = max_date
    for _ in range(24):
        for hour in range(24):
            date_hour_combinations.append((current_date, hour))
        current_date -= timedelta(days=1)
    
    # Fill in missing hours with zero counts
    filled_data = []
    for date, hour in date_hour_combinations:
        count = data_dict.get((date, hour), 0)
        filled_data.append((date, hour, count))
    
    return filled_data