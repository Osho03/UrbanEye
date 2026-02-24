from flask import Blueprint, jsonify
from config import db

features_bp = Blueprint("features", __name__)
feature_flags_collection = db["feature_flags"]

@features_bp.route("/status", methods=["GET"])
def get_feature_status():
    """
    Return the current status of all feature flags.
    Used by the mobile app for backend-driven UI updates.
    """
    try:
        # Get flags from DB
        flags = feature_flags_collection.find_one({}, {"_id": 0})
        
        # Default flags if collection is empty
        default_flags = {
            "forensic_ai_enabled": False,
            "cost_prediction_enabled": True,
            "impact_radius_enabled": True,
            "contractor_ai_enabled": False
        }
        
        if not flags:
            # Seed the database if no flags exist
            feature_flags_collection.insert_one(default_flags)
            return jsonify(default_flags)
            
        return jsonify(flags)
    except Exception as e:
        print(f"❌ Feature Flags Error: {e}")
        return jsonify({"error": str(e)}), 500
