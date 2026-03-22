import os
import asyncio
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CalendarService:
    def __init__(self):
        self.creds = None
        self.service = None
        self._load_credentials()

    def _load_credentials(self):
        token_path = os.path.join(_PROJECT_DIR, 'token.json')
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception:
                    self.creds = None
            else:
                self.creds = None

        if self.creds:
            self.service = build('calendar', 'v3', credentials=self.creds)

    async def get_upcoming_events(self):
        if not self.service:
            return ["10:00 AM - Design review (Mock)", "2:00 PM - Call with John (Mock)", "7:00 PM - Dinner (Mock)"]

        try:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            events_result = await asyncio.to_thread(
                self.service.events().list(calendarId='primary', timeMin=now,
                                           maxResults=5, singleEvents=True,
                                           orderBy='startTime').execute
            )
            events = events_result.get('items', [])

            if not events:
                return ["No upcoming events."]

            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                if 'T' in start:
                    dt = datetime.datetime.fromisoformat(start)
                    h = dt.hour % 12 or 12
                    ampm = "AM" if dt.hour < 12 else "PM"
                    date_str = dt.strftime("%b %d")
                    time_str = f"{date_str} {h}:{dt.minute:02d} {ampm}"
                else:
                    dt = datetime.date.fromisoformat(start)
                    time_str = f"{dt.strftime('%b %d')} All Day"

                summary = event.get('summary', '(No title)')
                formatted_events.append(f"\\[{time_str}] {summary}")
            return formatted_events
        except Exception as e:
            return [f"Calendar Error: {e}"]
