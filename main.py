import datetime
import os
import pickle
import google.auth
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Returns a service object that can be used to interact with Google Calendar API.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service

def get_meetings_of_week(service):
    # Get the current week (from Monday to Sunday)
    now = datetime.datetime.utcnow()
    start_of_week = now - datetime.timedelta(days=now.weekday())  # Monday
    end_of_week = start_of_week + datetime.timedelta(days=6)  # Sunday
    
    # Convert datetime to RFC3339 format
    start_of_week = start_of_week.isoformat() + 'Z'
    end_of_week = end_of_week.isoformat() + 'Z'

    print(f'Fetching meetings from {start_of_week} to {end_of_week}')

    events_result = service.events().list(calendarId='primary', timeMin=start_of_week,
                                          timeMax=end_of_week, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

def summarize_meetings(events):
    total_hours = 0
    summary = {}

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))

        start_time = datetime.datetime.fromisoformat(start)
        end_time = datetime.datetime.fromisoformat(end)

        # Calculate duration in hours
        duration = (end_time - start_time).total_seconds() / 3600.0
        total_hours += duration

        event_summary = event.get('summary', 'No Title')
        summary[event_summary] = summary.get(event_summary, 0) + duration

    print(f"Total hours in meetings this week: {total_hours:.2f}")
    return summary, total_hours

def main():
    # Authenticate and get service object for Google Calendar
    service = authenticate_google()

    # Get the meetings from the current week
    events = get_meetings_of_week(service)

    if not events:
        print('No meetings found.')
    else:
        summary, total_hours = summarize_meetings(events)
        print("\nSummary of meetings:")
        for event, hours in summary.items():
            print(f"{event}: {hours:.2f} hours")
        print(f"\nTotal hours spent in meetings this week: {total_hours:.2f} hours")

if __name__ == '__main__':
    main()