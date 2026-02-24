"""
UrbanEye Mobile User Authentication Routes
NEW endpoints for Flutter mobile app - does NOT modify existing routes
"""
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import hashlib
import uuid

user_bp = Blueprint("user", __name__)

# Database connection
client = MongoClient("mongodb://localhost:27017/")
db = client["urbaneye"]
users_collection = db["users"]
issues_collection = db["issues"]

def hash_password(password):
    """Simple SHA-256 password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

@user_bp.route("/register", methods=["POST"])
def register():
    """Register a new citizen user"""
    data = request.json
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    phone = data.get("phone", "")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email and password required"}), 400

    # Check if email already exists
    if users_collection.find_one({"email": email}):
        return jsonify({"success": False, "message": "Email already registered"}), 409

    user = {
        "name": name,
        "email": email,
        "password": hash_password(password),
        "phone": phone,
        "role": "citizen",
        "created_at": datetime.now(),
        "token": str(uuid.uuid4())
    }

    result = users_collection.insert_one(user)
    user_id = str(result.inserted_id)

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "user": {
            "user_id": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "role": "citizen",
            "token": user["token"]
        }
    }), 201

@user_bp.route("/login", methods=["POST"])
def login():
    """Login for citizen users"""
    data = request.json
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400

    user = users_collection.find_one({"email": email})
    if not user or user["password"] != hash_password(password):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    # Generate new token on each login
    new_token = str(uuid.uuid4())
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"token": new_token, "last_login": datetime.now()}}
    )

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": {
            "user_id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "phone": user.get("phone", ""),
            "role": user.get("role", "citizen"),
            "token": new_token
        }
    })

@user_bp.route("/profile/<user_id>", methods=["GET"])
def get_profile(user_id):
    """Get user profile"""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        return jsonify({
            "success": True,
            "user": {
                "user_id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "phone": user.get("phone", ""),
                "role": user.get("role", "citizen"),
                "created_at": user.get("created_at", "").isoformat() if user.get("created_at") else None
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@user_bp.route("/profile/<user_id>", methods=["PUT"])
def update_profile(user_id):
    """Update user profile"""
    data = request.json
    try:
        update_fields = {}
        if "name" in data:
            update_fields["name"] = data["name"].strip()
        if "phone" in data:
            update_fields["phone"] = data["phone"].strip()

        if not update_fields:
            return jsonify({"success": False, "message": "No fields to update"}), 400

        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )

        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Profile updated"})
        return jsonify({"success": False, "message": "No changes made"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@user_bp.route("/reports/<user_id>", methods=["GET"])
def get_user_reports(user_id):
    """Get all issues reported by a specific user"""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Find issues by reported_by name OR email
        issues = list(issues_collection.find({
            "$or": [
                {"reported_by": user["name"]},
                {"reporter_email": user["email"]}
            ]
        }).sort("created_at", -1))

        # Serialize
        for issue in issues:
            issue["issue_id"] = str(issue["_id"])
            del issue["_id"]
            # Convert datetime objects to strings
            if "created_at" in issue and issue["created_at"]:
                issue["created_at"] = issue["created_at"].isoformat()
            if "updated_at" in issue and issue["updated_at"]:
                issue["updated_at"] = issue["updated_at"].isoformat()

        return jsonify({
            "success": True,
            "count": len(issues),
            "issues": issues
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
