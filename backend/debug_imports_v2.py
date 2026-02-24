
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

print("--- DIAGNOSTIC START ---")

print("1. Testing Summarizer Import...")
try:
    from ai.summarizer import summarizer
    print("✅ Summarizer Imported Successfully")
except Exception as e:
    print(f"❌ Summarizer Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing Voice Synth Import...")
try:
    from ai.text_to_speech import voice_synth
    print("✅ Voice Synth Imported Successfully")
except Exception as e:
    print(f"❌ Voice Synth Failed: {e}")
    import traceback
    traceback.print_exc()

print("--- DIAGNOSTIC END ---")
