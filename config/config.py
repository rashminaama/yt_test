import os
from dotenv import load_dotenv

load_dotenv()

# ---- Database (Postgres) + YouTube (kept together per convention) ----
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "yt_trending")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
REGION_CODE = os.getenv("REGION_CODE", "US")

# ---- SMTP ----
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = True

# ---- Recipients ----
RECIPIENT_EMAILS = [
    e.strip() for e in os.getenv("RECIPIENT_EMAILS", "").split(",") if e.strip()
]

# ---- Dashboard auth (simple shared login) ----
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME")
DASHBOARD_PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH")  # generated with werkzeug, never plaintext
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# ---- Monitoring ----
HEALTHCHECKS_URL = os.getenv("HEALTHCHECKS_URL")
