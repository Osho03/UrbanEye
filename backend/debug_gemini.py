import google.generativeai as genai
import os

# usage: py -3.13 debug_gemini.py

def test_gemini():
    api_key = "AIzaSyA5Cei2ld_I2BQU8qvVdJ-SnOJL-SJfL6s"
    print(f"Testing Gemini with key: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        
        # Try generic gemini-flash-latest (Explicitly listed)
        model_name = 'gemini-flash-latest'
        print(f"\nAttempting to use model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        print("Sending request...")
        response = model.generate_content("Hello! Are you a static bot or a smart AI?")
        
        print("\n--- RESPONSE ---")
        print(response.text)
        print("----------------\n")
        print("[SUCCESS] Gemini is working.")
        
    except Exception as e:
        print(f"\n[FAILURE] {type(e).__name__}")
        print(e)

if __name__ == "__main__":
    test_gemini()
