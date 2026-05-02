from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Optional local .env loading (ignored on Render if file doesn't exist)
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

app = Flask(__name__)
# Allow UNLIMITED uploads (to fix 413 Errors completely)
app.config['MAX_CONTENT_LENGTH'] = None 
CORS(app, resources={r"/*": {"origins": "*"}})
from flask import jsonify

@app.errorhandler(500)
def handle_500(error):
    """Ensure JSON is returned on internal server error instead of HTML"""
    return jsonify({
        "error": "Internal Server Error",
        "message": str(error),
        "status": 500
    }), 500

from routes.issue import issue_bp
from routes.admin import admin_bp
from routes.analytics import analytics_bp

# Import new routes
try:
    from routes.chatbot import bp as chatbot_bp
    CHATBOT_AVAILABLE = True
except ImportError:
    print("⚠️  Chatbot routes not available")
    CHATBOT_AVAILABLE = False

from routes.user import user_bp
from routes.features import features_bp

app.register_blueprint(issue_bp, url_prefix="/api/issues")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(user_bp, url_prefix="/api/user")
app.register_blueprint(features_bp, url_prefix="/api/features")

# Register chatbot routes if available
if CHATBOT_AVAILABLE:
    app.register_blueprint(chatbot_bp)
    print("[INFO] Chatbot routes registered")

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded images"""
    # Defensive: If filename includes 'uploads/' or 'uploads\', strip it
    clean_name = filename.replace("uploads/", "").replace("uploads\\", "")
    return send_from_directory("uploads", clean_name)

@app.route("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "UrbanEye Backend is running"}, 200

# ==================== USER IMPACT ====================

@app.route('/api/user/impact/<user_id>', methods=['GET'])
def get_user_impact(user_id):
    try:
        # Sum of impact scores for all reports by this user
        reports = list(reports_collection.find({"user_id": user_id}))
        total_impact = sum(r.get('impact_score', 0) for r in reports)
        
        # Calculate rank
        rank = "Bronze Citizen"
        if total_impact > 500: rank = "Gold Guardian"
        elif total_impact > 200: rank = "Silver Sentinel"
        
        return jsonify({
            "success": True,
            "total_impact": total_impact,
            "rank": rank,
            "reports_count": len(reports)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Ensure backend uses dynamic port from environment (essential for Render)
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting UrbanEye Backend on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
