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
import os

user_bp = Blueprint("user", __name__)

from config import db
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
            "token": new_token,
            "profile_photo": user.get("profile_photo")
        }
    })

@user_bp.route("/google-login", methods=["POST"])
def google_login():
    """Simulated Google One-Tap Login"""
    data = request.json
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    profile_photo = data.get("profile_photo", "")

    if not email or not name:
        return jsonify({"success": False, "message": "Email and name required"}), 400

    user = users_collection.find_one({"email": email})
    
    if not user:
        # Create new user automatically from Google data
        user = {
            "name": name,
            "email": email,
            "profile_photo": profile_photo,
            "role": "citizen",
            "auth_type": "google",
            "created_at": datetime.now(),
            "token": str(uuid.uuid4())
        }
        result = users_collection.insert_one(user)
        user["_id"] = result.inserted_id
    else:
        # Update existing user with latest Google info
        new_token = str(uuid.uuid4())
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "name": name,
                "profile_photo": profile_photo if profile_photo else user.get("profile_photo"),
                "token": new_token,
                "last_login": datetime.now()
            }}
        )
        user["token"] = new_token

    return jsonify({
        "success": True,
        "message": "Google Login successful",
        "user": {
            "user_id": str(user["_id"]),
            "name": name,
            "email": email,
            "profile_photo": user.get("profile_photo"),
            "role": user.get("role", "citizen"),
            "token": user["token"]
        }
    })

@user_bp.route("/profile-photo/<user_id>", methods=["POST"])
def upload_profile_photo(user_id):
    """Upload or update profile photo"""
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "No image provided"}), 400
    
    image = request.files['image']
    if image.filename == '':
        return jsonify({"success": False, "message": "Empty filename"}), 400

    # Save image
    upload_dir = os.path.join("uploads", "profiles")
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"profile_{user_id}_{int(datetime.now().timestamp())}.jpg"
    filepath = os.path.join(upload_dir, filename)
    image.save(filepath)

    # Update DB
    photo_url = f"uploads/profiles/{filename}"
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_photo": photo_url}}
    )

    return jsonify({
        "success": True,
        "message": "Profile photo updated",
        "photo_url": photo_url
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
                "age": user.get("age"),
                "gender": user.get("gender"),
                "notifications_enabled": user.get("notifications_enabled", True),
                "notify_status_updates": user.get("notify_status_updates", True),
                "notify_digest": user.get("notify_digest", False),
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
        if "age" in data:
            try:
                update_fields["age"] = int(data["age"])
            except (TypeError, ValueError):
                return jsonify({"success": False, "message": "Age must be a number"}), 400
        if "gender" in data:
            update_fields["gender"] = data["gender"].strip()
        # Notification preferences
        if "notifications_enabled" in data:
            update_fields["notifications_enabled"] = bool(data["notifications_enabled"])
        if "notify_status_updates" in data:
            update_fields["notify_status_updates"] = bool(data["notify_status_updates"])
        if "notify_digest" in data:
            update_fields["notify_digest"] = bool(data["notify_digest"])

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

@user_bp.route('/notifications/<user_id>', methods=['GET'])
def get_user_notifications(user_id):
    """Aggregate status updates / notifications for all of a user's reports,
    newest first. Powers the mobile in-app real-time notification feed."""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        issues = list(issues_collection.find({
            "$or": [
                {"reported_by": user["name"]},
                {"reporter_email": user["email"]}
            ]
        }))

        items = []
        for iss in issues:
            issue_title = iss.get("title") or ""
            issue_type = iss.get("issue_type", "report")
            history = iss.get("status_history") or []
            # Walk backwards so the newest change sorts first
            for entry in reversed(history):
                raw_ts = entry.get("changed_at")
                if isinstance(raw_ts, datetime):
                    ts = raw_ts.isoformat() + "Z"
                else:
                    try:
                        ts = datetime.fromisoformat(str(raw_ts).replace("Z", ""))
                        ts = ts.isoformat() + "Z"
                    except (ValueError, TypeError):
                        ts = str(raw_ts)
                items.append({
                    "issue_id": str(iss["_id"]),
                    "issue_title": issue_title,
                    "issue_type": issue_type,
                    "status": entry.get("status"),
                    "comment": entry.get("comment"),
                    "changed_by": entry.get("changed_by", "System"),
                    "changed_at": ts,
                })

        try:
            items.sort(key=lambda x: x["changed_at"], reverse=True)
        except Exception:
            pass

        prefs = {
            "notifications_enabled": user.get("notifications_enabled", True),
            "notify_status_updates": user.get("notify_status_updates", True),
            "notify_digest": user.get("notify_digest", False),
        }

        return jsonify({
            "success": True,
            "count": len(items),
            "notifications": items,
            "prefs": prefs
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@user_bp.route('/impact/<user_id>', methods=['GET'])
def get_user_impact(user_id):
    """Calculate and return user impact score and rank"""
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Find all reports by this user to calculate impact
        reports = list(issues_collection.find({
            "$or": [
                {"reported_by": user["name"]},
                {"reporter_email": user["email"]}
            ]
        }))
        
        # Calculate total impact score
        # In a real app, this would use a more complex algorithm
        total_impact = sum(r.get('severity_score', 1) * 10 for r in reports)
        
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
        return jsonify({"success": False, "message": str(e)}), 500
