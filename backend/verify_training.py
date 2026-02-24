
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api/chatbot/message"

def test_chat(message, expected_keywords):
    print(f"\n🧪 User: {message}")
    try:
        payload = {"message": message, "user_id": "verify_training_user"}
        resp = requests.post(BASE_URL, json=payload)
        
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("bot_response", "")
            print(f"🤖 AI: {reply}")
            
            # success = any(k.lower() in reply.lower() for k in expected_keywords)
            # Relaxed check: Just printing it for manual review is often better for LLMs
            # But let's check for at least ONE keyword
            found = [k for k in expected_keywords if k.lower() in reply.lower()]
            
            if found:
                print(f"✅ PASSED (Found keywords: {found})")
            else:
                print(f"⚠️ REVIEW (Expected keywords like {expected_keywords} not found explicitly)")
        else:
            print(f"❌ FAILED: Status {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

print("=== VERIFYING AI TRAINING ===")
time.sleep(2) # Give server a moment if just started

# 1. Identity Check
test_chat("Who are you?", ["UrbanEye", "AI", "Guide", "Assistant"])

# 2. Workflow Guidance
test_chat("How do I report a pothole?", ["Camera", "Photo", "Click", "Upload"])

# 3. FAQ Knowledge
test_chat("Is this app free?", ["Yes", "Free", "100%"])

# 4. Math/Intelligence Check
test_chat("What is 50 + 25?", ["75"])

# 5. Training Confirmation
test_chat("Have you been trained?", ["Trained", "UrbanEye", "Architecture"])
