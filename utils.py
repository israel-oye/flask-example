import secrets
import string
import threading

from flask import current_app
from flask_mail import Message

# from app import mail


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