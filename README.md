# google-calendar-parser

This repository presents a solution where you can fetch your Google Calendar meetings, classify them and summarize them by using an AI.

## Setup and Running Locally

To run the `server.py` file locally, follow these steps:

1. **Clone the repository:**
   ```
   git clone https://github.com/your-username/google-calendar-parser.git
   cd google-calendar-parser
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install fastapi google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv pytz 
   ```

4. **Set up Google Calendar API:**
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Enable the Google Calendar API for your project.
   - Create a service account and download the JSON key file.
   - Rename the key file to `credentials.json` and place it in the project root directory.

5. **Configure environment variables:**
   Create a `.env` file in the project root directory with the following content:
   ```
   EMAIL=your-google-calendar-email@example.com
   ```

6. **Run the server:**
   ```
   fastapi run server.py
   ```

   The server will start running on `http://127.0.0.1:8000`.

7. **Access the API:**
   - Open a web browser or use a tool like curl to access the API endpoints:
     - Root endpoint: `http://127.0.0.1:8000/`
     - Calendar events endpoint: `http://127.0.0.1:8000/calendar-events?date=YYYY-MM-DD`

## API Endpoints

- `/`: Welcome message
- `/calendar-events`: Fetch and summarize calendar events
  - Query parameter: `date` (format: YYYY-MM-DD)

## Note

Make sure to grant the necessary permissions to your service account to access your Google Calendar. You may need to share your calendar with the service account email address.
