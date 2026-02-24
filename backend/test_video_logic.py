import requests
import os
import time

URL = "http://localhost:5000/api/issues/report"
VIDEO_PATH = "test_video.mp4"

# Create dummy video file
with open(VIDEO_PATH, "wb") as f:
    f.write(b"fake video content")

try:
    print("Testing Video Upload Logic...")
    with open(VIDEO_PATH, "rb") as f:
        files = {"image": f}
        data = {
            "title": "Video Report",
            "description": "Testing video upload flow",
            "latitude": "11.01",
            "longitude": "76.95"
        }
        res = requests.post(URL, files=files, data=data)
        
    if res.status_code == 200:
        result = res.json()
        print("✅ Upload Successful!")
        print(f"Detected Type: {result.get('issue_type')}")
        
        # Verify it was treated as video
        issue_id = result.get("issue_id")
        res_status = requests.get(f"http://localhost:5000/api/issues/{issue_id}/status")
        status_data = res_status.json()
        
        # Note: Status API filters fields, so we might not see media_type 
        # unless we update status API or check Admin remarks.
        # But report_issue sets 'admin_remarks' for video.
        
        remarks = status_data.get("admin_remarks", "")
        if "Video Analysis" in remarks:
            print("✅ Verified: System treated file as VIDEO")
        else:
            print(f"❌ Failed: System treated as IMAGE? Remarks: {remarks}")
            
    else:
        print(f"❌ Failed: {res.text}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if os.path.exists(VIDEO_PATH):
        os.remove(VIDEO_PATH)
