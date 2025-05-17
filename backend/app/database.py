from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from app.config import MONGO_URI, DB_NAME

# Set up MongoDB client using Server API v1 (recommended for Atlas)
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

# Ping MongoDB to ensure connection is successful
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Failed to connect to MongoDB:", e)
    raise e

# Database reference
db = client[DB_NAME]
