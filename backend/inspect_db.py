"""Inspect local vs possible cloud MongoDB contents."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import client, db, issues_collection

print(f"Connected host: {client.address}")
print(f"Database: {db.name}")

print("\n--- Collections ---")
for name in db.list_collection_names():
    print(f"  {name}: {db[name].count_documents({})} docs")

total = issues_collection.count_documents({})
annotated = issues_collection.count_documents({"detected_image": {"$exists": True, "$ne": None}})
with_photo = issues_collection.count_documents({"image_path": {"$ne": None}})
print(f"\nissues total={total} | with photo={with_photo} | annotated={annotated}")

print("\n--- Sample issues ---")
for d in issues_collection.find({}, {"issue_type": 1, "image_path": 1, "detected_image": 1, "created_at": 1}).limit(10):
    print(" ", {k: str(v)[:60] for k, v in d.items() if k != "_id"})
