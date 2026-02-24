import cv2
import numpy as np
from datetime import datetime, timedelta
from config import issues_collection

def compute_dhash(image_path, hash_size=8):
    """
    Compute the dHash (difference hash) of an image.
    Resizes to (hash_size + 1, hash_size), converts to grayscale,
    and compares adjacent pixels.
    """
    try:
        # Load image in grayscale
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return None
            
        # Resize to (width, height) = (hash_size + 1, hash_size)
        resized = cv2.resize(image, (hash_size + 1, hash_size))
        
        # Calculate difference between adjacent pixels
        diff = resized[:, 1:] > resized[:, :-1]
        
        # Convert boolean array to hex string
        # Pack bits into integer then hex
        return hex(int("".join(["1" if b else "0" for b in diff.flatten()]), 2))[2:]
    except Exception as e:
        print(f"Error computing dHash: {e}")
        return None

def hamming_distance(hash1, hash2):
    """
    Calculate Hamming distance between two hex strings.
    """
    if not hash1 or not hash2:
        return 999 # Max distance
    
    # Convert hex to integers
    try:
        n1 = int(hash1, 16)
        n2 = int(hash2, 16)
        
        # XOR and count set bits
        x = n1 ^ n2
        return bin(x).count('1')
    except:
        return 999

def find_potential_duplicate(current_hash, lat, lng, threshold=15):
    """
    Find if a similar issue exists near the location.
    
    Criteria:
    1. Within last 7 days.
    2. Within ~20 meters (approx 0.0002 degrees).
    3. Hamming distance < threshold.
    """
    if not current_hash or not lat or not lng:
        return None
        
    try:
        lat = float(lat)
        lng = float(lng)
        
        # 1. Time Filter: Last 7 days
        start_date = datetime.now() - timedelta(days=7)
        
        # 2. Geo Filter: Simple bounding box (approx 20-30m)
        lat_range = 0.0003 
        lng_range = 0.0003
        
        candidates = issues_collection.find({
            "created_at": {"$gte": start_date},
            "status": {"$ne": "Resolved"}, # Only match open issues
            "latitude": {"$ne": None},
            "longitude": {"$ne": None},
            "image_hash": {"$exists": True} # Must have a hash
        })
        
        for issue in candidates:
            # Check Geo manually (since we store strings, and simple float comp is strict)
            try:
                i_lat = float(issue.get("latitude"))
                i_lng = float(issue.get("longitude"))
                
                if abs(lat - i_lat) < lat_range and abs(lng - i_lng) < lng_range:
                    # Check Visual Similarity
                    dist = hamming_distance(current_hash, issue.get("image_hash"))
                    if dist < threshold:
                        return issue # Return the full duplicate object
            except:
                continue
                
        return None
    except Exception as e:
        print(f"Error finding duplicate: {e}")
        return None
