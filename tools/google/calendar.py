from . import get_google_service
from datetime import datetime, timezone

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_service():
    return get_google_service("calendar", "v3", SCOPES)


def list_events(limit=10):
    """Lista eventos futuros."""
    try:
        service = get_service()
        events = service.events().list(
            calendarId='primary', maxResults=limit,
            singleEvents=True, orderBy='startTime'
        ).execute()
        return [{"title": e.get("summary", "Sem título"), "start": e['start'].get('dateTime', e['start'].get('date'))}
                for e in events.get('items', [])]
    except Exception as e:
        return {"error": str(e), "cause": "Calendar API falhou"}


def today_events():
    """Eventos do dia atual."""
    try:
        service = get_service()
        now = datetime.now(timezone.utc)
        end = now.replace(hour=23, minute=59, second=59)
        events = service.events().list(
            calendarId='primary', timeMin=now.isoformat(), timeMax=end.isoformat(),
            singleEvents=True, orderBy='startTime'
        ).execute()
        return events.get('items', [])
    except Exception as e:
        return {"error": str(e), "cause": "Calendar API falhou"}


def create_event(summary, start_time, end_time, description="", attendees=None):
    """Cria evento no calendário."""
    try:
        service = get_service()
        event = {"summary": summary, "description": description,
                 "start": {"dateTime": start_time, "timeZone": "UTC"},
                 "end": {"dateTime": end_time, "timeZone": "UTC"}}
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        created = service.events().insert(calendarId="primary", body=event).execute()
        return {"success": True, "summary": summary, "start": start_time}
    except Exception as e:
        return {"error": str(e), "cause": "Calendar API falhou"}


def update_event(event_id, updates: dict):
    """Atualiza evento existente."""
    try:
        service = get_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        event.update(updates)
        return service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
    except Exception as e:
        return {"error": str(e), "cause": "Calendar API falhou"}


def delete_event(event_id):
    """Deleta evento por ID."""
    try:
        service = get_service()
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return {"status": "deleted", "event_id": event_id}
    except Exception as e:
        return {"error": str(e), "cause": "Calendar API falhou"}