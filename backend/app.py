from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Optional local .env loading
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None 
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def home():
    """Root route for Render's default health check"""
    return jsonify({"status": "live", "message": "UrbanEye API is online"}), 200

@app.route("/api/health")
def health_check():
    """Ultra-fast health check for Render"""
    return {"status": "ok", "message": "UrbanEye Live"}, 200

@app.errorhandler(500)
def handle_500(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

# Try/Except for Chatbot to prevent crash
try:
    from routes.chatbot import bp as chatbot_bp
    CHATBOT_AVAILABLE = True
except (ImportError, Exception):
    CHATBOT_AVAILABLE = False

# Lazy-load blueprints
from routes.issue import issue_bp
from routes.admin import admin_bp
from routes.analytics import analytics_bp
from routes.user import user_bp
from routes.features import features_bp

app.register_blueprint(issue_bp, url_prefix="/api/issues")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(user_bp, url_prefix="/api/user")
app.register_blueprint(features_bp, url_prefix="/api/features")

if CHATBOT_AVAILABLE:
    app.register_blueprint(chatbot_bp)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    clean_name = filename.replace("uploads/", "").replace("uploads\\", "")
    return send_from_directory("uploads", clean_name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
