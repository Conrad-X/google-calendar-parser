import requests
from datetime import datetime, timedelta

def get_start_of_week(date_str):
    # Parse the provided date string into a datetime object
    date = datetime.strptime(date_str, "%Y-%m-%d")

    # Calculate the start of the week (Monday) relative to the given date
    start_of_week = date - timedelta(days=date.weekday())
    return start_of_week.strftime("%Y-%m-%d")

def send_date_request(start_of_week_date):
    url = "https://google-calendar-automation-904b606de84f.herokuapp.com/events"
    params = {"date": start_of_week_date}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        print(f"Request successful! Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

# Example usage: fetch the current date or a given date
input_date = "2024-10-18"  # Example date
start_of_week_date = get_start_of_week(input_date)

print(f"Start of the week for `{input_date}` is {start_of_week_date}")

# Send the calculated start of the week date in the request
send_date_request(start_of_week_date)