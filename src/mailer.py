import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tenacity import retry, stop_after_attempt, wait_exponential

from config import config


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def send_report(html_body, subject="YouTube Trending — Daily Report"):
    if not config.RECIPIENT_EMAILS:
        raise ValueError("RECIPIENT_EMAILS is empty — nothing to send to")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = config.SMTP_USERNAME
    message["To"] = ", ".join(config.RECIPIENT_EMAILS)
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        if config.SMTP_USE_TLS:
            server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.sendmail(config.SMTP_USERNAME, config.RECIPIENT_EMAILS, message.as_string())
