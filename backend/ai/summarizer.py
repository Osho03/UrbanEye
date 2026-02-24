"""
Issue Summarization Engine
Generates concise summaries of citizen issue descriptions
Powered by Google Gemini (FREE)
"""

import os
import json

class IssueSummarizer:
    """
    AI-powered text summarization for issue descriptions
    Uses Google Gemini (Free Tier)
    """
    
    def __init__(self):
        # Import Gemini chatbot instance
        try:
            from ai.gemini_chatbot import init_gemini, gemini_chatbot
            if not gemini_chatbot:
                init_gemini()
                from ai.gemini_chatbot import gemini_chatbot
            self.ai = gemini_chatbot.model
            self.model_available = True
            print("[INFO] Summarizer using Google Gemini (FREE)")
        except Exception as e:
            print(f"[WARN] Gemini not available for summarizer: {e}")
            self.model_available = False
    
    def summarize(self, description, issue_type=None, location=None, severity=None):
        """
        Generate 1-2 sentence summary for admins
        """
        if not self.model_available:
            print("[INFO] Model unavailable. Using Local Intelligence Summary.")
            return self._generate_local_summary(description, issue_type, location, severity)
            
        # Build context
        context_parts = []
        if issue_type: context_parts.append(f"Issue Type: {issue_type}")
        if location: context_parts.append(f"Location: {location}")
        if severity: context_parts.append(f"Severity: {severity}")
        context = "\n".join(context_parts) if context_parts else "No metadata"
        
        prompt = f"""Summarize this civic issue in 1-2 sentences for government officials.
        
Context: {context}
Description: {description}

Return ONLY the summary."""
        
        try:
            # helper function to generate content using the chatbot's robust fallback mechanism
            # We can't use chat.send_message because this is a one-off task, not a chat.
            # So we use the model directly BUT with the same retry logic.
            # ACTUALLY: Best to expose a 'generate_content' method on GeminiChatbot to reuse the logic.
            # For now, let's look at how GeminiChatbot is implemented.
            # It uses self.model.start_chat() or self.model.generate_content()
            
            # Let's import the global instance and use its primary model, 
            # BUT we need to implement the same loop here or add a method to GeminiChatbot.
            # To keep it clean, I will try the primary, then manual fallback here.
            
            print(f"[INFO] Summarizing with {self.ai.model_name}...")
            response = self.ai.generate_content(prompt)
            return response.text.strip().strip('"')

        except Exception as e:
            print(f"[WARN] Primary summarizer failed: {e}. Trying backups...")
            # Manual fallback loop for summarizer (similar to chatbot)
            backup_names = ['gemini-1.5-flash', 'gemini-1.5-pro']
            import google.generativeai as genai
            
            for name in backup_names:
                try:
                    print(f"[INFO] 🔄 Backup Summarizer: Switching to {name}...")
                    backup_model = genai.GenerativeModel(name)
                    response = backup_model.generate_content(prompt)
                    return response.text.strip().strip('"')
                except Exception as backup_error:
                    print(f"[WARN] Backup {name} failed: {backup_error}")
                    continue
            
            print(f"[WARN] Cloud Summarizer failed. using Local Intelligence Summary.")
            return self._generate_local_summary(description, issue_type, location, severity)

    def generate_generative_summary(self, description, location, image_caption="No image caption provided"):
        """
        ✨ GENERATIVE AI MODE (Toggle OFF)
        Uses the specific prompt requested for Generative Assistant.
        """
        if not self.model_available:
            return self._generate_local_summary(description)

        prompt = f"""You are an AI Civic Assistant helping city administrators.

Analyze the following citizen complaint and perform:

1. Identify issue type
2. Summarize complaint in formal language
3. Suggest responsible department
4. Suggest urgency level (Low/Medium/High)

Citizen Complaint:
{description}

Location:
{location}

Image Description:
{image_caption}

Output Format:
Issue Type:
Summary:
Suggested Department:
Urgency Level:"""

        try:
            print("[INFO] ✨ GEN MODE: Running Generative Prompt...")
            response = self.ai.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[WARN] Generative Mode Failed: {e}")
            return f"Error: {str(e)}"

    def _generate_local_summary(self, description, issue_type=None, location=None, severity=None):
        """
        Generates a professional summary locally using sentence templates.
        Guarantees a valid summary even without Internet/Cloud-AI.
        """
        # Clean inputs
        issue_str = issue_type if issue_type else "civic maintenance issue"
        loc_str = f" at {location}" if location else ""
        sev_str = f"A {severity} severity" if severity else "A reported"
        
        # Extract meaningful keywords (simple implementation)
        desc_words = description.split()
        important_words = [w for w in desc_words if len(w) > 4][:5]
        details = ", ".join(important_words)
        
        # Construct summary templates
        if len(description) > 10:
             summary = f"{sev_str} {issue_str} has been identified{loc_str}. The report describes: '{description[:50]}...'. Immediate verification is recommended."
        else:
             summary = f"{sev_str} {issue_str} requires attention{loc_str}. Local teams should investigate this report to ensure public safety."
             
        return summary
    
    def extract_key_points(self, description):
        """
        Extract structured information from issue description
        """
        # Production Mode: No Fallback
        if not self.model_available:
            return {"error": "AI Service Unavailable"}
            
        prompt = f"""Extract key info from this civic report: "{description}"
        
Return JSON with:
- problem: short description of damage
- location_mentioned: specific location or null
- urgency_indicators: list of urgency words used
- keywords: list of top 5 keywords
- estimated_urgency: "high", "medium", or "low"
"""
        
        try:
            response = self.ai.generate_content(prompt)
            text = response.text.strip()
            # Clean up markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                
            return json.loads(text)
            
        except Exception as e:
            print(f"[ERROR] Extraction error: {e}")
            return {"error": f"AI Parsing Error: {str(e)}"}

    def generate_admin_briefing(self, issue_data):
        """
        Generate comprehensive admin briefing
        """
        description = issue_data.get('description', 'No description')
        summary = self.summarize(
            description,
            issue_type=issue_data.get('issue_type'),
            location=issue_data.get('location'),
            severity=issue_data.get('severity_label')
        )
        
        key_points = self.extract_key_points(description)
        
        briefing = f"""
**Quick Summary**: {summary}

**Key Information**:
- Problem: {key_points.get('problem', 'Unknown')}
- Urgency: {key_points.get('estimated_urgency', 'medium').upper()}
- Keywords: {', '.join(key_points.get('keywords', [])[:5])}
"""
        if key_points.get('location_mentioned'):
            briefing += f"- Location: {key_points['location_mentioned']}\n"
            
        return briefing.strip()

# Initialize global summarizer
summarizer = IssueSummarizer()
