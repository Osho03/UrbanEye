"""
FREE Rule-Based Chatbot for UrbanEye
No API key required - works completely offline!
"""

import re
from datetime import datetime

class FreeChatbot:
    """
    Smart rule-based chatbot with pattern matching
    No external APIs needed - 100% FREE!
    """
    
    def __init__(self):
        self.knowledge_base = self._build_knowledge_base()
        self.conversations = {}
    
    def _build_knowledge_base(self):
        """
        Comprehensive Q&A knowledge base about UrbanEye
        """
        return {
            # How to report issues
            "report": {
                "keywords": ["report", "submit", "upload", "send", "file", "how do i", "how to"],
                "response": """📸 **How to Report an Issue:**

1. Open the UrbanEye app
2. Click the camera icon or upload a photo
3. Your location is captured automatically
4. Add a description (optional)
5. Click "Submit"!

Our AI will detect the issue type automatically (pothole, garbage, etc.). You'll get updates via email if you provide one! 😊"""
            },
            
            # Issue types
            "types": {
                "keywords": ["what can", "issue types", "report what", "kinds of", "types of"],
                "response": """🏙️ **You Can Report These Issues:**

🕳️ **Potholes** - Road damage, cracks
💡 **Streetlights** - Broken lights
🗑️ **Garbage** - Waste accumulation
💧 **Water Leaks** - Pipe bursts
🚶 **Sidewalk Damage** - Broken pavements
🌊 **Drainage** - Blocked drains, flooding

Just take a photo and our AI will identify it!"""
            },
            
            # Timeline
            "time": {
                "keywords": ["how long", "when", "timeline", "duration", "days", "weeks"],
                "response": """⏰ **Resolution Timeline:**

- **Average**: 5-7 days
- **Urgent issues**: 1-3 days
- **Non-urgent**: Up to 2 weeks

You'll get email updates when:
✅ Issue is assigned
✅ Work starts (In Progress)
✅ Issue is resolved!"""
            },
            
            # Account/Login
            "account": {
                "keywords": ["account", "login", "sign up", "register", "password"],
                "response": """🔓 **No Account Needed!**

UrbanEye is completely anonymous:
✅ No sign-up required
✅ No password needed
✅ Just upload and report!

Email is optional (only for update notifications). Your reports are tracked automatically! 😊"""
            },
            
            # Updates/Status
            "status": {
                "keywords": ["update", "status", "track", "check", "progress", "my reports"],
                "response": """📊 **Check Your Reports:**

1. Click "My Reports" in the app
2. See all your submissions
3. Check current status:
   - 📥 Pending
   - ✅ Verified
   - 🔄 In Progress
   - ✅ Resolved

If you provided email, you'll get automatic updates!"""
            },
            
            # AI Accuracy
            "accuracy": {
                "keywords": ["accurate", "ai", "wrong", "detection", "correct", "mistake"],
                "response": """🤖 **AI Accuracy:**

Our AI model is **85% accurate**!

❓ What if it's wrong?
→ No worries! Government admins review ALL submissions and can correct the category.

💡 The AI learns from corrections and gets better over time!"""
            },
            
            # Privacy/Data
            "privacy": {
                "keywords": ["privacy", "safe", "data", "secure", "personal"],
                "response": """🔒 **Your Privacy is Protected:**

We ONLY store:
✅ Photo
✅ GPS location
✅ Description (if provided)

We DON'T store:
❌ Name (unless you add it)
❌ Phone number
❌ Personal information

All data is encrypted and used only for fixing city issues! 🛡️"""
            },
            
            # Greeting
            "greeting": {
                "keywords": ["hi", "hello", "hey", "good morning", "good evening"],
                "response": """👋 Hello! I'm the UrbanEye Assistant!

I can help you with:
📸 How to report issues
🏙️ What you can report
⏰ Resolution timelines
📊 Checking your reports
🔒 Privacy & data safety

What would you like to know?"""
            },
            
            # Thanks
            "thanks": {
                "keywords": ["thank", "thanks", "appreciate"],
                "response": """You're welcome! 😊

Happy to help make our city better! If you see any infrastructure problems, don't hesitate to report them. Every report helps! 🏙️✨"""
            },
            
            # Help/General
            "help": {
                "keywords": ["help", "assist", "support", "don't understand"],
                "response": """🆘 **I'm Here to Help!**

Common questions:
1️⃣ How do I report an issue?
2️⃣ What can I report?
3️⃣ How long until it's fixed?
4️⃣ Do I need an account?
5️⃣ How do I check my reports?

Just ask me anything about UrbanEye! 😊"""
            }
        }
    
    def chat(self, user_id, message):
        """
        Process user message and return smart response
        
        Args:
            user_id: User identifier
            message: User's message
            
        Returns:
            Bot's response
        """
        # Initialize conversation history
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Add user message to history
        self.conversations[user_id].append({
            "role": "user",
            "content": message
        })
        
        # Find best matching response
        response = self._match_intent(message.lower())
        
        # Add bot response to history
        self.conversations[user_id].append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _match_intent(self, message):
        """
        Match user message to knowledge base using keyword matching
        """
        # Check each category
        for category, data in self.knowledge_base.items():
            for keyword in data["keywords"]:
                if keyword in message:
                    return data["response"]
        
        # Default response if no match
        return """I'm here to help with UrbanEye! 😊

Try asking:
- "How do I report an issue?"
- "What can I report?"
- "How long does it take?"
- "Do I need to create an account?"

What would you like to know?"""
    
    def clear_conversation(self, user_id):
        """Clear conversation history"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            return True
        return False
    
    def get_quick_replies(self):
        """Get suggested quick reply buttons"""
        return [
            "How do I report?",
            "What can I report?",
            "How long to fix?",
            "Check my reports",
            "Do I need login?"
        ]


# Initialize global FREE chatbot instance
free_chatbot = FreeChatbot()
