import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing. Check your .env file.")
if not MONGO_URI:
    raise ValueError("MONGO_URI is missing. Check your .env file.")
if not DB_NAME:
    raise ValueError("DB_NAME is missing. Check your .env file.")