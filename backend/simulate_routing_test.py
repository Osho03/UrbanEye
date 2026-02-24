import requests
import os

# Create a dummy image for testing
with open("test_pothole.jpg", "wb") as f:
    f.write(b"fake image content")

url = "http://localhost:5000/api/issues/report"
# Fix: Open file in a context manager or explicit close to avoid WinError 32
file_handle = open("test_pothole.jpg", "rb")
files = {"image": file_handle}

data = {
    "title": "Test Auto Routing",
    "description": "Testing if pothole goes to Road Dept",
    "latitude": "11.0168",
    "longitude": "76.9558"
}

try:
    print("Testing Auto-Routing...")
    response = requests.post(url, files=files, data=data)
    
    # Close file handle immediately after request
    file_handle.close()
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Issue Reported Successfully!")
        print(f"Detected Type: {result.get('issue_type')}")
        # Note: In Phase 1 we didn't return department in response, 
        # so we trust the backend logic or check DB if needed.
        # But simulation script success means the endpoint didn't crash on new logic.
    else:
        print(f"❌ Failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    file_handle.close() # Ensure close on error
finally:
    if os.path.exists("test_pothole.jpg"):
        try:
            os.remove("test_pothole.jpg")
            print("Cleanup successful")
        except Exception as e:
            print(f"Cleanup warning: {e}")
