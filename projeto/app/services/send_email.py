import smtplib
import os
from pathlib import Path

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from dotenv import load_dotenv

from jinja2 import Environment, FileSystemLoader

load_dotenv()
env = Environment(loader=FileSystemLoader("app/templates"))
LOGO_PATH = Path("frontend/static/images/MENTISTECH_logo.png")


def build_email_body(data, template_type):
    template = env.get_template(f"emails/{template_type}_email.html")

    return template.render(
        {
            "user_name": data.user_name,
            "user_email": data.user_email,
            "user_id": data.user_id,
            "message": data.message,
        }
    )


def send_email(subject, sender_email, email_to, reply_to, body):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart("related")
    msg["From"] = f"MentisTech <{sender_email}>"
    msg["To"] = email_to
    msg["Reply-To"] = reply_to
    msg["Subject"] = subject

    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(body, "html"))
    msg.attach(alternative)

    if LOGO_PATH.exists():
        with LOGO_PATH.open("rb") as logo_file:
            logo = MIMEImage(logo_file.read())
            logo.add_header("Content-ID", "<mentistech_logo>")
            logo.add_header("Content-Disposition", "inline", filename=LOGO_PATH.name)
            msg.attach(logo)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
