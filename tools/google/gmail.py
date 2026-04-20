from . import get_google_service
import base64
import re
from email.mime.text import MIMEText

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_service():
    return get_google_service("gmail", "v1", SCOPES)


def list_emails(max_results=5):
    """Lista emails não lidos."""
    try:
        service = get_service()
        results = service.users().messages().list(
            userId='me', maxResults=max_results, labelIds=['INBOX'], q="is:unread"
        ).execute()
        emails = []
        for msg in results.get('messages', []):
            full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = full_msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "")
            emails.append({"id": msg["id"], "subject": subject, "from": sender, "snippet": full_msg.get("snippet", "")})
        return emails
    except Exception as e:
        return {"error": str(e), "cause": "Gmail API falhou"}


def read_email(message_id):
    """Lê email completo por ID."""
    try:
        service = get_service()
        return service.users().messages().get(userId='me', id=message_id).execute()
    except Exception as e:
        return {"error": str(e), "cause": "Gmail API falhou"}


def reply_email(message_id, reply_text):
    """Responde email preservando thread."""
    try:
        service = get_service()
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        headers = message['payload']['headers']
        original_subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "")
        original_from = next((h['value'] for h in headers if h['name'] == 'From'), "")
        original_to = next((h['value'] for h in headers if h['name'] == 'To'), "")

        email_match = re.search(r'<([^>]+)>', original_from)
        reply_to = email_match.group(1) if email_match else original_from

        from_match = re.search(r'<([^>]+)>', original_to)
        reply_from = from_match.group(1) if from_match else original_to

        mime_msg = MIMEText(reply_text)
        mime_msg['to'] = reply_to
        mime_msg['from'] = reply_from
        mime_msg['subject'] = original_subject if original_subject.startswith("Re:") else f"Re: {original_subject}"

        encoded_msg = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
        send_message = service.users().messages().send(userId='me', body={'raw': encoded_msg}).execute()
        return {"success": True, "message_id": send_message.get('id'), "to": reply_to, "subject": mime_msg['subject']}
    except Exception as e:
        return {"error": str(e), "cause": "Gmail API falhou"}


def delete_email(message_id):
    """Deleta email por ID."""
    try:
        service = get_service()
        service.users().messages().delete(userId='me', id=message_id).execute()
        return {"status": "deleted", "message_id": message_id}
    except Exception as e:
        return {"error": str(e), "cause": "Gmail API falhou"}


def compose_email(to: str, subject: str, body: str):
    """Cria e envia novo email."""
    try:
        service = get_service()
        mime_msg = MIMEText(body)
        mime_msg['to'] = to
        mime_msg['subject'] = subject
        encoded_msg = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
        send_message = service.users().messages().send(userId='me', body={'raw': encoded_msg}).execute()
        return {"success": True, "message_id": send_message.get('id'), "to": to, "subject": subject}
    except Exception as e:
        return {"error": str(e), "cause": "Gmail API falhou"}