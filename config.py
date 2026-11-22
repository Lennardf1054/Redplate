import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "quickserve.db")
SECRET_KEY = os.environ.get("QUICKSERVE_SECRET", "dev-only-change-me")
ADMIN_USERNAME = os.environ.get("QUICKSERVE_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("QUICKSERVE_ADMIN_PASSWORD", "admin123")

# Student sign-in with a school Google account.
# Put the real values in environment variables, never in this file.
ALLOWED_EMAIL_DOMAIN = os.environ.get("QUICKSERVE_ALLOWED_DOMAIN", "g.batstate-u.edu.ph")
GOOGLE_CLIENT_ID = os.environ.get("QUICKSERVE_GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("QUICKSERVE_GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("QUICKSERVE_GOOGLE_REDIRECT_URI", "")   # optional
GOOGLE_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
# Demo sign-in (type any school email, no Google). On by default only when Google is not set up.
DEMO_LOGIN = os.environ.get("QUICKSERVE_DEMO_LOGIN", "0" if GOOGLE_ENABLED else "1") == "1"
