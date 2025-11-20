from pymongo.mongo_client import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_URI")
print(f"Attempting to connect to MongoDB...")
print(f"URI (hidden password): {uri.replace(uri.split(':')[2].split('@')[0], '****')}")

# Try without ServerApi specification
client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"An error occurred: {str(e)}")