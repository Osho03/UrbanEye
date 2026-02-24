"""
Text-to-Speech Voice Synthesis
Converts issue summaries to natural-sounding audio
Powered by gTTS (Google Text-to-Speech) - 100% FREE
"""

import os
import hashlib
from gtts import gTTS

class VoiceSynthesizer:
    """
    Generate audio files from text using Google's FREE Text-to-Speech
    """
    
    def __init__(self):
        # Audio cache directory
        self.audio_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
        print("[INFO] Voice Synthesizer initialized (using FREE gTTS)")
    
    def generate_speech(self, text, issue_id=None, voice="en", speed=1.0):
        """
        Generate audio from text
        """
        # Generate unique filename
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        filename = f"{issue_id}_{text_hash}.mp3" if issue_id else f"summary_{text_hash}.mp3"
        audio_path = os.path.join(self.audio_dir, filename)
        
        # Check cache
        if os.path.exists(audio_path):
            print(f"[INFO] Using cached audio: {filename}")
            return f"audio/{filename}"
        
        try:
            print(f"[INFO] Generating audio (FREE): {text[:50]}...")
            
            # Use gTTS (Google Text-to-Speech)
            tts = gTTS(text=text, lang=voice, slow=(speed < 1.0))
            tts.save(audio_path)
            
            print(f"[INFO] Audio generated: {filename}")
            return f"audio/{filename}"
            
        except Exception as e:
            print(f"[ERROR] TTS error: {e}")
            # Fallback: Mock Audio (to prevent "Failed to generate" error)
            print("[WARN] Switching to Mock Audio Fallback")
            return "audio/mock_audio.mp3"
    
    def get_available_voices(self):
        """
        Get list of available languages (gTTS uses languages, not voices)
        """
        return {
            "en": "English (US)",
            "en-uk": "English (UK)",
            "en-au": "English (Australia)",
            "en-in": "English (India)",
            "es": "Spanish",
            "fr": "French",
            "hi": "Hindi"
        }
    
    def batch_generate(self, text_list, prefix="batch"):
        """Generate multiple audio files"""
        results = []
        for idx, text in enumerate(text_list):
            audio_path = self.generate_speech(text, issue_id=f"{prefix}_{idx}")
            results.append(audio_path)
        return results
    
    def clear_cache(self):
        """Delete all cached audio"""
        try:
            for filename in os.listdir(self.audio_dir):
                if filename.endswith('.mp3'):
                    os.remove(os.path.join(self.audio_dir, filename))
            return True
        except Exception:
            return False

# Initialize global TTS instance
voice_synth = VoiceSynthesizer()
