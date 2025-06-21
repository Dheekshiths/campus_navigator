# utils/sms_service.py
from twilio.rest import Client

def send_sms_notification(phone_to, message, account_sid, auth_token, phone_from):
    """Send SMS using Twilio"""
    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=phone_from,
            to=phone_to
        )
        return True
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return False