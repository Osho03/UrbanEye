"""
Quick script to test MongoDB connection
Run: python test_mongodb.py
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

try:
    # Use configuration from config.py to test the ACTUAL connection
    from config import MONGO_URI
    print(f"🔄 Connecting to: {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI}")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Force connection to verify it's working
    client.admin.command('ping')
    
    print("✅ SUCCESS: MongoDB is running and connected!")
    print(f"   Server: mongodb://localhost:27017")
    
    # List databases
    dbs = client.list_database_names()
    print(f"   Available databases: {dbs}")
    
    # Check if urbaneye database exists
    if "urbaneye" in dbs:
        db = client["urbaneye"]
        collections = db.list_collection_names()
        print(f"   UrbanEye collections: {collections}")
        
        # Count issues
        if "issues" in collections:
            count = db["issues"].count_documents({})
            print(f"   Total issues in database: {count}")
    else:
        print("   Note: 'urbaneye' database will be created on first insert")
    
except ConnectionFailure:
    print("❌ ERROR: Cannot connect to MongoDB")
    print("   Make sure MongoDB is running on localhost:27017")
    print("   Start MongoDB with: mongod")
    
except ServerSelectionTimeoutError:
    print("❌ ERROR: MongoDB connection timeout")
    print("   MongoDB is not running or not accessible")
    print("   To start MongoDB:")
    print("   - Windows: Run 'mongod' or start MongoDB service")
    print("   - Check if MongoDB is installed: mongod --version")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
