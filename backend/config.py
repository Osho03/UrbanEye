from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["urbaneye"]
issues_collection = db["issues"]
