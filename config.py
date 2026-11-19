import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "quickserve.db")
SECRET_KEY = os.environ.get("QUICKSERVE_SECRET", "dev-only-change-me")

ADMIN_USERNAME = os.environ.get("QUICKSERVE_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("QUICKSERVE_ADMIN_PASSWORD", "admin123")
