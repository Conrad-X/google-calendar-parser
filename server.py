from http.client import HTTPException
from fastapi import FastAPI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import os

load_dotenv()
app = FastAPI()

EMAIL = os.getenv("EMAIL")

# Path to the service account JSON key file
SERVICE_ACCOUNT_FILE = 'credentials.json'

# Scopes required for the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TIMEZONE = 'Asia/Karachi'

# Load credentials from the service account file
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Google Calendar service instance
service = build('calendar', 'v3', credentials=credentials)

# Meeting Ignore list
MEETING_IGNORE_LIST = [
    "Office",
    "Home",
    "Break - Lunch Time",
    "Break - Table Tennis",
    "Break - Jumma Prayer",
]

FYP_ADVISORY_COUNT = 0
RESEARCH_AND_DEVELOPMENT_COUNT = 0
OTHER_MEETING_COUNT = 0
ENGINEERING_FRAMEWORK_COUNT = 0
CONRADX_COUNT = 0

def add_working_days(start_date, working_days):
    """
    Adds working days (skipping weekends) to the start date.
    """
    current_date = start_date
    days_added = 0

    while days_added < working_days:
        current_date += timedelta(days=1)
        # Skip weekends
        if current_date.weekday() < 5:
            days_added += 1
    
    return current_date

@app.get("/calendar-events")
async def get_calendar_events(date: str):
    """
    Fetch calendar events for the full working day (9 AM to 5 PM) starting from the given date.
    
    :param date: Date in the format 'YYYY-MM-DD'
    :return: List of events during working hours on the given date
    """
    global FYP_ADVISORY_COUNT, RESEARCH_AND_DEVELOPMENT_COUNT, OTHER_MEETING_COUNT, ENGINEERING_FRAMEWORK_COUNT, CONRADX_COUNT
    
    # Reset counters at the beginning of the function
    FYP_ADVISORY_COUNT = 0
    RESEARCH_AND_DEVELOPMENT_COUNT = 0
    OTHER_MEETING_COUNT = 0
    ENGINEERING_FRAMEWORK_COUNT = 0
    CONRADX_COUNT = 0

    attendance_status = False

    try:
        # Parse the input date
        start_date = datetime.strptime(date, '%Y-%m-%d')

        # Add 5 working days to calculate the end date
        end_date = add_working_days(start_date, 4)
        
        # Define working hours (9 AM to 10 PM)
        start_time = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Convert to the appropriate timezone
        tz = pytz.timezone(TIMEZONE)
        start_time = tz.localize(start_time)
        end_time = tz.localize(end_time)
        
        # Convert to ISO 8601 format for Google Calendar API
        start_time_iso = start_time.isoformat()
        end_time_iso = end_time.isoformat()
        
        # Fetch events from Google Calendar within the time range
        events_result = service.events().list(
            calendarId=EMAIL, 
            timeMin=start_time_iso,
            timeMax=end_time_iso,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
         
        events = events_result.get('items', [])
        formatted_events = []

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # convert start and end to hours 
            start_time = datetime.fromisoformat(start.rstrip('Z'))
            end_time = datetime.fromisoformat(end.rstrip('Z'))
            duration = (end_time - start_time).total_seconds() / 3600

            # check if the event invite is accepted
            attendance_status = None
            if 'attendees' in event:
                for attendee in event['attendees']:
                    if attendee['email'] == EMAIL and attendee['responseStatus'] == 'accepted':
                        attendance_status = True
                # If the attendee is not accepted, set attendance_status to False
                if attendance_status is not True:
                    attendance_status = False

            # Check if the event is not in the ignore list and the attendance status is true or none
            if (event['summary'] not in MEETING_IGNORE_LIST) and (attendance_status == True or attendance_status == None):
                event_object = {
                    'summary': event['summary'],
                    'start': start,
                    'end': end,
                    'duration': duration,
                    'attendance_status': attendance_status
                }

                # Add description to the event object if it exists
                if 'description' in event:
                    event_object['description'] = event['description']

                # Add duration to the respective counter
                if "FYP Advisory -" in event['summary']:
                    FYP_ADVISORY_COUNT += duration
                elif "R&D -" in event['summary']:
                    RESEARCH_AND_DEVELOPMENT_COUNT += duration
                elif "Engineering Framework Support -" in event['summary']:
                    ENGINEERING_FRAMEWORK_COUNT += duration
                elif "ConradX -" in event['summary']:
                    CONRADX_COUNT += duration
                else:
                    OTHER_MEETING_COUNT += duration

                formatted_events.append(event_object)

        if not formatted_events:
            return {"message": "No events found for this date."}
        
        allocationObject = [
            {
                "name": "R&D / Pre-Sales (Solution building, Internal team standups)",
                "duration": RESEARCH_AND_DEVELOPMENT_COUNT,
                "percentage": float(RESEARCH_AND_DEVELOPMENT_COUNT/40) * 100
            },
            {
                "name": "Pre-Sales & Demo Meetings",
                "duration": OTHER_MEETING_COUNT,
                "percentage": float(OTHER_MEETING_COUNT/40) * 100
            },
            {
                "name": "Engineering framework support (Team CDCC & Simplistic)",
                "duration": ENGINEERING_FRAMEWORK_COUNT,
                "percentage": float(ENGINEERING_FRAMEWORK_COUNT/40) * 100
            },
            {
                "name": "ConradX / Substack",
                "duration": CONRADX_COUNT,
                "percentage": float(CONRADX_COUNT/40) * 100
            },
            {
                "name": "Fast FYP Advisory",
                "duration": FYP_ADVISORY_COUNT,
                "percentage": float(FYP_ADVISORY_COUNT/40) * 100
            }
        ]

        print("--------------------------------------------------------------------------------------------------------------------------------")
        print(f"R&D / Pre-Sales (Solution building, Internal team standups) : {RESEARCH_AND_DEVELOPMENT_COUNT} hours - {float(RESEARCH_AND_DEVELOPMENT_COUNT/40) * 100} %")
        print(f"Pre-Sales & Demo Meetings: {OTHER_MEETING_COUNT} hours - {float(OTHER_MEETING_COUNT/40) * 100} %")
        print(f"Engineering framework support (Team CDCC & Simplistic): {ENGINEERING_FRAMEWORK_COUNT} hours - {float(ENGINEERING_FRAMEWORK_COUNT/40) * 100} %")
        print(f"Fast FYP Advisory: {FYP_ADVISORY_COUNT} hours - {float(FYP_ADVISORY_COUNT/40) * 100} %")
        print(f"ConradX / Substack : {CONRADX_COUNT} hours - {float(CONRADX_COUNT/40) * 100} %")
        print("--------------------------------------------------------------------------------------------------------------------------------")
        
        # Return the list of events
        return {"allocation": allocationObject}
    
    except Exception as e:
        return {"error": str(e)}
