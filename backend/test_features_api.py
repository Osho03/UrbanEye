import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_features_api():
    print("🔍 Testing Features API...")
    try:
        response = requests.get(f"{BASE_URL}/features/status")
        if response.statusCode == 200:
            print("✅ Status Code: 200")
            print(f"🚩 Flags: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Failed: {response.statusCode}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_features_api()
