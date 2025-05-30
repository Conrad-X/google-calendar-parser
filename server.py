from http.client import HTTPException
from fastapi import FastAPI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import os
import json

from utility.read_spreadsheet import fetch_google_sheet_records

load_dotenv()
app = FastAPI()

# Email of the user of your google calendar
EMAIL = os.getenv("EMAIL")
GOOGLE_ALLOCATION_SHEET_NAME = os.getenv("GOOGLE_ALLOCATION_SHEET_NAME")
GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS_PATH"))

# Scopes required for the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TIMEZONE = 'Asia/Karachi'

# Load credentials from the service account file
credentials = service_account.Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
print(f"Google Service Account Connection Established.")

# Google Calendar service instance
service = build('calendar', 'v3', credentials=credentials)
print(f"Google Calendar Service Initialized.")

# Meeting Ignore list
MEETING_IGNORE_LIST = [
    "Office", # This corresponds to the office location
    "Home", # This corresponds to the home location
    "Break - Lunch Time",
    "Break - Table Tennis",
    "Break - Jumma Prayer",
]

# Counters
RESEARCH_AND_DEVELOPMENT_COUNT = 0
AI_SQUAD_MEETINGS = 0
CATALYST_HUB_MEETINGS = 0
PRE_SALES_MEETINGS = 0
CONRADX_COUNT = 0
INTERVIEW_COUNT = 0
OTHER_MEETING_COUNT = 0

# Work Week Configuration
WORK_WEEK = float(os.getenv("WORK_WEEK_HOURS"))

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

def generate_allocation_object():
    """
    Generate the allocation object
    """
    global AI_SQUAD_MEETINGS, CATALYST_HUB_MEETINGS, RESEARCH_AND_DEVELOPMENT_COUNT, PRE_SALES_MEETINGS, CONRADX_COUNT, INTERVIEW_COUNT, OTHER_MEETING_COUNT
    allocationObject = [
        {
            "name": "R&D Meetings (Solution building, Internal team standups)",
            "duration": round(RESEARCH_AND_DEVELOPMENT_COUNT, 2),
            "percentage": round(float(RESEARCH_AND_DEVELOPMENT_COUNT/WORK_WEEK) * 100, 2)
        },
        {
            "name": "Pre-Sales Meetings",
            "duration": round(PRE_SALES_MEETINGS, 2),
            "percentage": round(float(PRE_SALES_MEETINGS/WORK_WEEK) * 100, 2)
        },
        {
            "name": "AI-Squad Meetings",
            "duration": round(AI_SQUAD_MEETINGS, 2),
            "percentage": round(float(AI_SQUAD_MEETINGS/WORK_WEEK) * 100, 2)
        },
        {
            "name": "ConradX / Substack",
            "duration": CONRADX_COUNT,
            "percentage": round(float(CONRADX_COUNT/WORK_WEEK) * 100, 2)
        },
        {
            "name": "Catalyst-Hub Mentoring Meetings",
            "duration": round(CATALYST_HUB_MEETINGS, 2),
            "percentage": round(float(CATALYST_HUB_MEETINGS/WORK_WEEK) * 100, 2)
        },
        {
            "name": "Interviews",
            "duration": round(INTERVIEW_COUNT, 2),
            "percentage": round(float(INTERVIEW_COUNT/WORK_WEEK) * 100, 2)
        }
    ]

    print("-----------------------------------------------------------------------------------------------------------")
    print(f"R&D (Solution building, Internal team standups) : {RESEARCH_AND_DEVELOPMENT_COUNT} hours - {float(RESEARCH_AND_DEVELOPMENT_COUNT/WORK_WEEK) * 100} %")
    print(f"Pre-Sales Meetings : {PRE_SALES_MEETINGS} hours - {float(PRE_SALES_MEETINGS/WORK_WEEK) * 100} %")
    print(f"AI-Squad Meetings : {AI_SQUAD_MEETINGS} hours - {float(AI_SQUAD_MEETINGS/WORK_WEEK) * 100} %")
    print(f"Catalyst-Hub Mentoring Meetings : {CATALYST_HUB_MEETINGS} hours - {float(CATALYST_HUB_MEETINGS/WORK_WEEK) * 100} %")
    print(f"ConradX / Substack : {CONRADX_COUNT} hours - {float(CONRADX_COUNT/WORK_WEEK) * 100} %")
    print(f"Interviews : {INTERVIEW_COUNT} hours - {float(INTERVIEW_COUNT/WORK_WEEK) * 100} %")
    print("-----------------------------------------------------------------------------------------------------------")
    
    return allocationObject

def update_counters(event_summary, duration):
    """
    Update the counters based on the event summary
    """
    global AI_SQUAD_MEETINGS, CATALYST_HUB_MEETINGS, RESEARCH_AND_DEVELOPMENT_COUNT, PRE_SALES_MEETINGS, CONRADX_COUNT, INTERVIEW_COUNT, OTHER_MEETING_COUNT
    # Add duration to the respective counter
    if "Pre-Sales -" in event_summary or "Daily Pre-Sales" in event_summary:
        PRE_SALES_MEETINGS += duration
    elif "AI Squad -" in event_summary or "AI Daily" in event_summary:
        AI_SQUAD_MEETINGS += duration
    elif "Catalyst-Hub -" in event_summary or "Catalyst hub" in event_summary:
        CATALYST_HUB_MEETINGS += duration
    elif "R&D -" in event_summary:
        RESEARCH_AND_DEVELOPMENT_COUNT += duration
    elif "ConradX -" in event_summary:
        CONRADX_COUNT += duration
    elif "Interview" in event_summary:
        INTERVIEW_COUNT += duration
    else:
        OTHER_MEETING_COUNT += duration

@app.get("/")
async def root():
    return {"message": "Welcome to the Google Calendar API"}

@app.get("/allocation")
async def get_allocation():
    return fetch_google_sheet_records(GOOGLE_ALLOCATION_SHEET_NAME)

@app.get("/events")
async def get_calendar_events(date: str):
    """
    Fetch calendar events for the full working day (9 AM to 5 PM) starting from the given date.
    
    :param date: Date in the format 'YYYY-MM-DD'
    :return: List of events during working hours on the given date
    """
    global AI_SQUAD_MEETINGS, CATALYST_HUB_MEETINGS, RESEARCH_AND_DEVELOPMENT_COUNT, PRE_SALES_MEETINGS, CONRADX_COUNT, INTERVIEW_COUNT, OTHER_MEETING_COUNT
    
    # Reset counters at the beginning of the function
    AI_SQUAD_MEETINGS = 0
    RESEARCH_AND_DEVELOPMENT_COUNT = 0
    CATALYST_HUB_MEETINGS = 0
    PRE_SALES_MEETINGS = 0
    CONRADX_COUNT = 0
    INTERVIEW_COUNT = 0

    attendance_status = False

    try:
        # Parse the input date
        start_date = datetime.strptime(date, '%Y-%m-%d')

        # Add 5 working days to calculate the end date
        end_date = add_working_days(start_date, 4)
        
        # Define working hours (9 AM to 11 PM)
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

        # Format the events
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
                # Update the counters
                update_counters(event['summary'], duration)
                formatted_events.append(event_object)

        if not formatted_events:
            return {"message": "No events found for this date."}
        
        calendar_meeting_allocations = generate_allocation_object()

        # Return the list of events
        return {"allocation": calendar_meeting_allocations}
    
    except Exception as e:
        return {"error": str(e)}
