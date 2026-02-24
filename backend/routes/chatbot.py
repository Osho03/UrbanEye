"""
Chatbot API Routes
Endpoints for AI assistant conversations
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

# Import the chatbot engine
try:
    from ai.chatbot_engine import chatbot
except ImportError:
    print("⚠️  Chatbot engine not available - install openai: pip install openai")
    chatbot = None

bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

@bp.route('/message', methods=['POST'])
def send_message():
    """
    Send message to chatbot and get response
    
    POST /api/chatbot/message
    Body: {
        "user_id": "optional-user-id",
        "message": "How do I report a pothole?"
    }
    
    Response: {
        "user_message": "...",
        "bot_response": "...",
        "timestamp": "..."
    }
    """
    if not chatbot:
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
        bot_response = chatbot.chat(user_id, message)
        
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
    if not chatbot:
        return jsonify({"error": "Chatbot not available"}), 503
    
    success = chatbot.clear_conversation(user_id)
    
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
    if not chatbot:
        return jsonify({"quick_replies": []}), 503
    
    quick_replies = chatbot.get_quick_replies()
    
    return jsonify({
        "quick_replies": quick_replies
    })


@bp.route('/health', methods=['GET'])
def health_check():
    """
    Check if chatbot service is available
    
    GET /api/chatbot/health
    """
    return jsonify({
        "service": "chatbot",
        "status": "available" if chatbot else "unavailable",
        "message": "Chatbot ready" if chatbot else "OpenAI API key not configured"
    })
