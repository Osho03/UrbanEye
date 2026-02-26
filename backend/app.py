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

if __name__ == "__main__":
    # Ensure backend uses dynamic port from environment (essential for Render)
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting UrbanEye Backend on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
