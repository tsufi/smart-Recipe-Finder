# services/email_service.py
import os
import requests

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_BASE_URL = f"https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}"


def send_email(to, subject, text):
    if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
        raise RuntimeError("Missing Mailgun API configuration.")

    return requests.post(
        f"{MAILGUN_BASE_URL}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"RecipeFinder <{os.getenv('MAIL_DEFAULT_SENDER')}>",
            "to": to,
            "subject": subject,
            "text": text
        }
    )
