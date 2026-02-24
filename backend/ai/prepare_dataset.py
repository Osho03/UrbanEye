"""
Dataset Preparation Script for UrbanEye AI
Human-in-the-Loop Learning System

This script collects verified uploaded images from MongoDB and organizes them
into class-specific folders for training. This is the first phase of the
two-phase ML system: preparing labeled training data from user uploads.

Usage:
    python ai/prepare_dataset.py

Output:
    ai/dataset/
        ├── pothole/
        ├── garbage/
        ├── water_leak/
        └── streetlight/
"""

import shutil
import os
from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017")
db = client["urbaneye"]
issues = db["issues"]

# Dataset directory structure
BASE_DATASET = "ai/dataset"
CLASSES = ["pothole", "garbage", "water_leak", "streetlight"]

# Create class directories
for class_name in CLASSES:
    os.makedirs(os.path.join(BASE_DATASET, class_name), exist_ok=True)

print("🔄 Preparing training dataset from uploaded images...")
print("=" * 60)

# Statistics
stats = {class_name: 0 for class_name in CLASSES}
skipped = 0

# Collect images from MongoDB
for issue in issues.find({"issue_type": {"$ne": "unknown"}}):
    image_path = issue.get("image_path")
    issue_type = issue.get("issue_type")
    
    # Validate data
    if not image_path or not issue_type:
        skipped += 1
        continue
    
    # Check if image file exists
    if not os.path.exists(image_path):
        print(f"⚠️  Image not found: {image_path}")
        skipped += 1
        continue
    
    # Check if issue type is valid
    if issue_type not in CLASSES:
        print(f"⚠️  Invalid issue type: {issue_type}")
        skipped += 1
        continue
    
    # Copy image to appropriate class folder
    dest_dir = os.path.join(BASE_DATASET, issue_type)
    filename = os.path.basename(image_path)
    dest_path = os.path.join(dest_dir, filename)
    
    # Avoid duplicates
    if os.path.exists(dest_path):
        print(f"ℹ️  Already exists: {dest_path}")
        continue
    
    # Copy file
    shutil.copy(image_path, dest_path)
    stats[issue_type] += 1
    print(f"✅ Copied: {image_path} → {dest_path}")

print("=" * 60)
print("📊 Dataset Preparation Complete!")
print()
print("Class Distribution:")
for class_name, count in stats.items():
    print(f"  {class_name:15s}: {count:3d} images")
print(f"  {'Skipped':15s}: {skipped:3d} images")
print()

total_images = sum(stats.values())
print(f"Total training images: {total_images}")

if total_images < 20:
    print()
    print("⚠️  WARNING: Very few training images!")
    print("   Recommendation: Collect at least 50-100 images per class")
    print("   for meaningful model improvement.")
elif total_images < 100:
    print()
    print("ℹ️  Note: Dataset is small. Model may overfit.")
    print("   Recommendation: Collect more images for better accuracy.")
else:
    print()
    print("✅ Dataset size is sufficient for training!")

print()
print("Next step: Run 'python ai/train_model.py' to fine-tune the model")
