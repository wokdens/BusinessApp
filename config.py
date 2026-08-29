import os
import sys

# Handle both development and PyInstaller bundle environments
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure required application directories exist
DB_DIR = os.path.join(BASE_DIR, "database")
INVOICES_DIR = os.path.join(BASE_DIR, "invoices")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(INVOICES_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

DATABASE_PATH = os.path.join(DB_DIR, "business.db")