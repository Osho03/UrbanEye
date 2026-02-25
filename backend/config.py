import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load local .env for development
load_dotenv()

# Use Cloud URI if available, otherwise fallback to local
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["urbaneye"]
issues_collection = db["issues"]
