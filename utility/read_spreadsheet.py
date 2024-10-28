import gspread
import os
import pandas as pd
import json
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv()

def fetch_google_sheet_records(sheet_name:str):
    GOOGLE_CREDENTIALS = json.loads(os.getenv("GOOGLE_CREDENTIALS_PATH"))

    # Define the scope and create a credentials object
    SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=SCOPES)
    client = gspread.authorize(creds)

    # Open the Google Sheet
    spreadsheet = client.open(sheet_name)  # Replace with your sheet name
    worksheet = spreadsheet.sheet1  # You can also specify a sheet by name

    # Get all data from the worksheet
    data = worksheet.get_all_records()

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data)
    formatted_data = []
    formatted_string = "<ul>"

    for index, row in df.iterrows():
        formatted_row = row.to_dict()
        formatted_string += f"<li><b>{formatted_row['Name']}</b> - <a href='{formatted_row['Link']}'>{formatted_row['Project']}</a> ({formatted_row['Allocation']}%)</li>"
        formatted_data.append(formatted_row)

    formatted_string += "</ul>"
    return formatted_string
