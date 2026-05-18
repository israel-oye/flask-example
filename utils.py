import json
import os
import secrets
import string
import threading

import requests
from dotenv import load_dotenv
# from flask import current_app
# from flask_mail import Message


# from app import mail
load_dotenv()

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

def generate_random_otp(length: int):
    """Generates a random OTP"""
    random_digits = [secrets.choice(string.digits) for _ in range(length)]
    return "".join(random_digits)


# def send_email(message: Message):
#     with current_app.app_context():
#         mail.send(message)

# def send_mail_async(message: Message):
#     thread = threading.Thread(target=send_email, args=(message,))
#     thread.start()
#     thread.join()

def send_registration_mail(
        to: str, 
        username: str,
        otp: str,
        html_content: str
    ):
    payload = {
            "sender": {"name": "Flask App", "email": "ioyeboade@gmail.com"},
            "to": [{"email": to, "name": username}],
            "subject": f"Verify Account: Your OTP is {otp}",
            "htmlContent": html_content
        }

    response = requests.post(
        url=BREVO_URL,
        headers={
            'accept': "application/json",
            'content-type': "application/json",
            'api-key': os.getenv("BREVO_API_KEY")
        },
        data=json.dumps(payload)
    )

    return response
