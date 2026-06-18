import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production-to-a-random-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
