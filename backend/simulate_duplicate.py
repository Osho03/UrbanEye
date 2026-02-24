import requests
import time
import os
import shutil

# Setup
URL = "http://localhost:5000/api/issues/report"
IMG_PATH = "test_duplicate.jpg"

# Create dummy image (needs to be valid for opencv to open, so let's try to copy a real one or make a valid header)
# Implementing a minimal valid JPG header or using existing file
# For safety, let's assume there's no valid jpg handy and create a tiny valid one or use previous artifacts
# Actually, let's just create a text file as jpg might fail cv2.imread. 
# BUT wait, the code uses cv2.imread. If it fails, hash is None, and logic skips.
# We need a REAL image.
# I will try to generate a valid simple BMP or similar using python if possible, or hope cv2 can read a dummy.
# Actually, cv2 cannot read random bytes. 
# Let's try to use the previously uploaded 'test_pothole.jpg' if it exists or use a byte string for a valid tiny GIF/PNG.

# Tiny valid PNG
simple_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

with open(IMG_PATH, "wb") as f:
    f.write(simple_png)

try:
    # 1. Report Original
    print("Reporting Original Issue...")
    with open(IMG_PATH, "rb") as f:
        res1 = requests.post(URL, files={"image": f}, data={
            "title": "Original Pothole",
            "latitude": "12.9716",
            "longitude": "77.5946"
        })
    id1 = res1.json().get("issue_id")
    print(f"Original ID: {id1}")
    
    time.sleep(1)
    
    # 2. Report Duplicate (Same Image, Same Loc)
    print("Reporting Duplicate Issue...")
    with open(IMG_PATH, "rb") as f:
        res2 = requests.post(URL, files={"image": f}, data={
            "title": "Duplicate Pothole",
            "latitude": "12.9716",
            "longitude": "77.5946"
        })
    
    data2 = res2.json()
    id2 = data2.get("issue_id")
    print(f"Duplicate ID: {id2}")
    
    # 3. Verify
    if data2.get("message") == "Issue linked to existing report":
        print("✅ Success: API identified duplicate message")
    else:
        print(f"❌ Failed: API message is {data2.get('message')}")
        
    if data2.get("linked_to") == id1:
        print(f"✅ Success: Linked correctly to {id1}")
    else:
        print(f"❌ Failed: Linked to {data2.get('linked_to')}")
        
    # Check Support Count of Original
    res_status = requests.get(f"http://localhost:5000/api/issues/{id1}/status")
    # Note: Status API doesn't return support_count by default in Phase 3 code 
    # but we can check if we added it? No we didn't add it to status endpoint.
    # We might need to inspect DB or trust the write logic.
    # Actually, let's update Issue Detail to show verification if we can.
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists(IMG_PATH):
        os.remove(IMG_PATH)
