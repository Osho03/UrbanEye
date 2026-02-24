import requests
import json
import os
import time

# 1. Report an issue
print("Step 1: Reporting Issue...")
url_report = "http://localhost:5000/api/issues/report"
file_path = "test_myreports.jpg"

# Create dummy image
with open(file_path, "wb") as f:
    f.write(b"fake image")

try:
    with open(file_path, "rb") as f:
        files = {"image": f}
        data = {
            "title": "My Report Test",
            "description": "Testing My Reports feature",
            "latitude": "11.01",
            "longitude": "76.95"
        }
        res_report = requests.post(url_report, files=files, data=data)
    
    if res_report.status_code == 200:
        issue_id = res_report.json().get("issue_id")
        print(f"✅ Reported! ID: {issue_id}")
        
        # 2. Check Status (Client Simulation)
        print("Step 2: Checking Status API...")
        time.sleep(1) # Wait for DB
        
        url_status = f"http://localhost:5000/api/issues/{issue_id}/status"
        res_status = requests.get(url_status)
        
        if res_status.status_code == 200:
            status_data = res_status.json()
            print("✅ Status Fetched!")
            print(json.dumps(status_data, indent=2))
            
            if status_data.get("status") == "Pending":
                print("✅ Verification Passed: Issue is Pending")
            else:
                print("❌ Verification Failed: Status mismatch")
        else:
            print(f"❌ Failed to fetch status: {res_status.text}")

    else:
        print(f"❌ Failed to report: {res_report.text}")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if os.path.exists(file_path):
        os.remove(file_path)
