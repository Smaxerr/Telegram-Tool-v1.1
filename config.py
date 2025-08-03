import os
from dotenv import load_dotenv

load_dotenv()  # This loads environment variables from .env file

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, filter(None, os.getenv("ADMIN_IDS", "").split(","))))


DB_CONFIG = {
    "user": os.getenv("PGUSER"),
    "password": os.getenv("PGPASSWORD"),
    "database": os.getenv("PGDATABASE"),
    "host": os.getenv("PGHOST"),
    "port": int(os.getenv("PGPORT", 5432)),
}
