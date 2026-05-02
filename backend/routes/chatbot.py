"""
Chatbot API Routes
Endpoints for AI assistant conversations
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

# Global chatbot instance for lazy loading
chatbot = None

def get_chatbot():
    """Lazy initialize the chatbot engine"""
    global chatbot
    if chatbot is None:
        try:
            from ai.chatbot_engine import UrbanEyeChatbot
            chatbot = UrbanEyeChatbot()
        except Exception as e:
            print(f"❌ Error initializing chatbot engine: {e}")
            chatbot = "ERROR" # Marker to prevent repeated failing attempts
    return chatbot

bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@bp.route('/message', methods=['POST'])
def send_message():
    """
    Send message to chatbot and get response
    """
    bot = get_chatbot()
    if bot is None or bot == "ERROR":
        return jsonify({"error": "Chatbot not available. Please configure OpenAI API key."}), 503
    
    data = request.json
    
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    message = data.get('message', '').strip()
    user_id = data.get('user_id', str(uuid.uuid4()))  # Generate random ID if not provided
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        # Get bot response
        bot_response = bot.chat(user_id, message)
        
        return jsonify({
            "success": True,
            "user_message": message,
            "bot_response": bot_response,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Chatbot error: {e}")
        return jsonify({
            "error": "Failed to generate response",
            "details": str(e)
        }), 500


@bp.route('/clear/<user_id>', methods=['POST'])
def clear_conversation(user_id):
    """
    Clear conversation history for a user
    
    POST /api/chatbot/clear/<user_id>
    """
    bot = get_chatbot()
    if bot is None or bot == "ERROR":
        return jsonify({"error": "Chatbot not available"}), 503
    
    success = bot.clear_conversation(user_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Conversation cleared"
        })
    else:
        return jsonify({
            "success": False,
            "message": "No conversation found for this user"
        })


@bp.route('/quick-replies', methods=['GET'])
def get_quick_replies():
    """
    Get suggested quick reply buttons
    
    GET /api/chatbot/quick-replies
    """
    bot = get_chatbot()
    if bot is None or bot == "ERROR":
        return jsonify({"quick_replies": []}), 503
    
    quick_replies = bot.get_quick_replies()
    
    return jsonify({
        "quick_replies": quick_replies
    })


@bp.route('/health', methods=['GET'])
def health_check():
    """
    Check if chatbot service is available
    
    GET /api/chatbot/health
    """
    bot = get_chatbot()
    is_avail = bot is not None and bot != "ERROR"
    return jsonify({
        "service": "chatbot",
        "status": "available" if is_avail else "unavailable",
        "message": "Chatbot ready" if is_avail else "Chatbot engine initialization failed"
    })
