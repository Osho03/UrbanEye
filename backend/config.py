import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Optional local .env loading (ignored on Render if file doesn't exist)
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Use Cloud URI if available, otherwise fallback to local
# Render will provide MONGO_URI directly in the environment
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = None
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    # Trigger a ping to verify connection works
    client.admin.command('ping')
    print("Successfully connected to MongoDB Cloud/Local")
except Exception as e:
    print(f"MongoDB Connection Error with {MONGO_URI}: {e}")
    print("Falling back to local MongoDB (mongodb://localhost:27017)...")
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=10000)
        client.admin.command('ping')
        print("Successfully connected to local MongoDB")
    except Exception as e2:
        print(f"Local MongoDB also failed: {e2}")
        # Last resort - create client anyway, app will fail gracefully on DB operations
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)

db = client["urbaneye"]
issues_collection = db["issues"]
