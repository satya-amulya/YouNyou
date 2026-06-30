from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timezone
import os

def get_calendar_service(access_token: str):
    creds = Credentials(token=access_token)
    return build("calendar", "v3", credentials=creds)

def get_todays_events(access_token: str) -> list:
    """Pull today's Google Calendar events to match against tasks."""
    service = get_calendar_service(access_token)
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0).isoformat()
    end = now.replace(hour=23, minute=59, second=59).isoformat()
    
    events = service.events().list(
        calendarId="primary",
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    result = []
    for e in events.get("items", []):
        start_t = e["start"].get("dateTime", e["start"].get("date"))
        end_t = e["end"].get("dateTime", e["end"].get("date"))
        if "T" in str(start_t) and "T" in str(end_t):
            s = datetime.fromisoformat(start_t.replace("Z", "+00:00"))
            en = datetime.fromisoformat(end_t.replace("Z", "+00:00"))
            duration_hours = (en - s).seconds / 3600
            result.append({
                "title": e.get("summary", ""),
                "duration_hours": round(duration_hours, 2),
                "start": s.isoformat(),
            })
    return result

def push_task_to_calendar(access_token: str, task_title: str, scheduled_date: datetime, estimated_hours: float):
    """Push a roadmap task as a Google Calendar event."""
    service = get_calendar_service(access_token)
    start = scheduled_date.replace(hour=9, minute=0)  # default 9am
    from datetime import timedelta
    end = start + timedelta(hours=estimated_hours)
    
    event = {
        "summary": f"[YouNYou] {task_title}",
        "description": "Auto-scheduled by YouNYou AI",
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        "colorId": "9",  # blueberry
    }
    service.events().insert(calendarId="primary", body=event).execute()