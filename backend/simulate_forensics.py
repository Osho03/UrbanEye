import requests
import os
from PIL import Image

# 1. Create a dummy image (No EXIF)
img = Image.new('RGB', (100, 100), color = 'red')
img.save('no_exif_test.jpg')

# 2. Prepare Payload
url = "http://localhost:5000/api/issues/report"
files = {'image': open('no_exif_test.jpg', 'rb')}
data = {
    "title": "Forensics Test - No EXIF",
    "description": "Testing if system handles missing metadata correctly.",
    "latitude": "11.00",
    "longitude": "76.00"
}

# 3. Send Request
try:
    print("Sending request...")
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print("Response:", response.json())
except Exception as e:
    print(f"Error: {e}")
finally:
    files['image'].close()
    # Cleanup
    if os.path.exists('no_exif_test.jpg'):
        os.remove('no_exif_test.jpg')
