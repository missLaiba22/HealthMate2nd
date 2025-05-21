from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from app.config import MONGO_URI, DB_NAME
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up MongoDB client using Server API v1 (recommended for Atlas)
try:
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    logger.info("MongoDB client initialized successfully")

    # Ping MongoDB to ensure connection is successful
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB!")

    # Database reference
    db = client[DB_NAME]
    logger.info(f"Using database: {DB_NAME}")

    # Verify collections exist
    collections = db.list_collection_names()
    logger.info(f"Available collections: {collections}")

    # Ensure conversations collection exists
    if 'conversations' not in collections:
        db.create_collection('conversations')
        logger.info("Created conversations collection")

except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise e
