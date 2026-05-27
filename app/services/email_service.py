import smtplib
from email.message import EmailMessage

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings

_jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html"]),
)


def render_email(template_name: str, context: dict) -> str:
    return _jinja_env.get_template(template_name).render(**context)


def send_email(to: str, subject: str, html_body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_username}>"
    msg["To"] = to
    msg.set_content("Please view this email in an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_app_password)
        smtp.send_message(msg)


def send_daily_email(to: str, context: dict) -> None:
    html = render_email("emails/daily.html", context)
    streak = context["user"].current_streak
    subject = f"LeetStreak — Day {streak + 1}: {context['question'].title}"
    send_email(to, subject, html)
