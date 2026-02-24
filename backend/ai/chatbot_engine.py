"""
UrbanEye AI Chatbot Engine
Intelligent assistant with domain knowledge about the UrbanEye app
MULTI-TIER AI: Gemini (FREE) → OpenAI (Premium)
"""

import os
from datetime import datetime

class UrbanEyeChatbot:
    """
    Conversational AI assistant:
    1. Google Gemini (FREE, recommended!)
    2. OpenAI GPT (if you have billing)
    """
    
    def __init__(self):
        self.chatbot_type = None
        self.chatbot = None
        
        # Try Gemini first (FREE!)
        if self._init_gemini():
            self.chatbot_type = "gemini"
            print("[INFO] Using Google Gemini AI (FREE tier)")
            return
        
        # Try OpenAI second (requires billing)
        if self._init_openai():
            self.chatbot_type = "openai"
            print("[INFO] Using OpenAI GPT (premium mode)")
            return
        
        # Fallback to FREE rule-based chatbot (no API key needed!)
        try:
            from ai.free_chatbot import FreeChatbot
            self.chatbot = FreeChatbot()
            self.chatbot_type = "free"
            print("[INFO] ✅ Using FREE rule-based chatbot (no API key needed)")
            return
        except Exception as e:
            print(f"⚠️ Free chatbot failed: {e}")
        
        # If even free chatbot fails, go offline
        print("[WARN] No chatbot available at all.")
        self.chatbot_type = "offline"
        self.chatbot = None
    
    def _init_gemini(self):
        """Try to initialize Gemini AI"""
        try:
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key and len(gemini_key) > 20:
                from ai.gemini_chatbot import init_gemini
                if init_gemini():
                    from ai.gemini_chatbot import gemini_chatbot
                    self.chatbot = gemini_chatbot
                    return True
        except Exception as e:
            print(f"⚠️ Gemini not available: {e}")
        return False
    
    def _init_openai(self):
        """Try to initialize OpenAI"""
        try:
            # Check for valid key pattern
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and api_key.startswith('sk-') and len(api_key) > 20:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.system_prompt = self._build_knowledge_base()
                self.conversations = {}
                return True
        except Exception as e:
            print(f"⚠️ OpenAI not available: {e}")
        return False
    
    def _build_knowledge_base(self):
        """
        Complete UrbanEye domain knowledge for the chatbot
        Note: Gemini uses its own internal system prompt, this is for OpenAI.
        """
        return """You are UrbanEye AI, an intelligent civic governance assistant.

**About UrbanEye**:
UrbanEye helps citizens report infrastructure problems to the government using AI-powered photo analysis.

**How It Works**:
1. Citizens take/upload a photo of the problem
2. Our AI automatically detects what type of issue it is
3. GPS location is captured automatically  
4. Issue is sent to the correct government department
5. Citizens get email updates until it's fixed

**Issue Types We Handle**:
- 🕳️ Pothole
- 💡 Streetlight
- 🗑️ Garbage
- 💧 Water Leak
- 🚶 Sidewalk Damage
- 🌊 Drainage

**Important**:
- Be professional and concise.
- Provide accurate information.
- Do NOT make up information."""
    
    def chat(self, user_id, message):
        """
        Process user message with best available AI
        Priority: Gemini (FREE) → OpenAI (Premium)
        """
        if self.chatbot_type == "offline":
             return "[System Error] No AI service configured. Please check server logs or API keys."

        # Use FREE rule-based chatbot
        if self.chatbot_type == "free":
            try:
                return self.chatbot.chat(user_id, message)
            except Exception as e:
                return f"[Chat Error] {str(e)}"

        # Use Gemini
        if self.chatbot_type == "gemini":
            try:
                return self.chatbot.chat(user_id, message)
            except Exception as e:
                return f"[AI Service Error] Gemini Unavailable: {str(e)}"
        
        # Use OpenAI
        if self.chatbot_type == "openai":
            if user_id not in self.conversations:
                self.conversations[user_id] = []
            
            self.conversations[user_id].append({
                "role": "user",
                "content": message
            })
            
            context = self.conversations[user_id][-10:]
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        *context
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                bot_message = response.choices[0].message.content.strip()
                
                self.conversations[user_id].append({
                    "role": "assistant",
                    "content": bot_message
                })
                
                return bot_message
                
            except Exception as e:
                print(f"[ERROR] OpenAI failed: {e}")
                return f"[AI Service Error] OpenAI Unavailable: {str(e)}"
        
        return "[System Error] Unknown AI State"
    
    def clear_conversation(self, user_id):
        """Clear conversation history"""
        if self.chatbot_type in ("gemini", "free"):
            return self.chatbot.clear_conversation(user_id)
        elif self.chatbot_type == "openai" and user_id in self.conversations:
            del self.conversations[user_id]
        return True
    
    def get_quick_replies(self):
        """Get suggested quick replies"""
        if self.chatbot:
            return self.chatbot.get_quick_replies()
        return [
            "How do I report?",
            "What can I report?",
            "How long to fix?",
            "Check my reports",
            "Do I need login?"
        ]

# Initialize global chatbot instance
chatbot = UrbanEyeChatbot()
