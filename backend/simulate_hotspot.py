import requests
import random
import time

URL = "http://localhost:5000/api/issues/report"

# Base coordinates
LAT = 11.0150
LON = 76.9550

print("🔥 Simulating Hotspot (5 Potholes in 10m radius)...")

for i in range(5):
    # Add tiny jitter (approx 1-5 meters)
    lat_jitter = random.uniform(-0.00005, 0.00005)
    lon_jitter = random.uniform(-0.00005, 0.00005)
    
    data = {
        "title": f"Pothole Cluster #{i+1}",
        "description": "Part of simulated hotspot test",
        "latitude": str(LAT + lat_jitter),
        "longitude": str(LON + lon_jitter)
    }
    
    # We need to send an image (dummy)
    with open("test_pothole_hotspot.jpg", "wb") as f:
        f.write(b"fake image data") # Content doesn't matter for clustering
        
    with open("test_pothole_hotspot.jpg", "rb") as f:
        files = {"image": f}
        try:
            res = requests.post(URL, files=files, data=data)
            if res.status_code == 200:
                print(f"✅ Report {i+1}/5 Submitted: {res.json().get('issue_id')}")
            else:
                print(f"❌ Failed: {res.text}")
        except Exception as e:
            print(f"Error: {e}")
            
    time.sleep(0.5)

print("\n🌍 Checking Analytics Endpoint...")
try:
    res = requests.get("http://localhost:5000/api/analytics/hotspots")
    hotspots = res.json()
    print(f"🔍 Detected Hotspots: {len(hotspots)}")
    for h in hotspots:
        print(f"   -> Recommendation: {h['recommendation']}")
        print(f"   -> Count: {h['count']}")
except Exception as e:
    print(f"Error checking analytics: {e}")
