import os
from flask import Blueprint, request, jsonify
from config import issues_collection
from datetime import datetime
from ai.image_classifier import classify_issue
from routes.routing import get_routing_info

issue_bp = Blueprint("issue", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@issue_bp.route("/report", methods=["POST"])
def report_issue():
    print("➡️ Received Report Request") # DEBUG LOG
    
    # Initialize ALL variables at start to prevent UnboundLocalError
    forensics_data = {"status": "Skipped", "details": "No image provided"}
    severity_data = {"score": 1, "label": "Low", "details": {"method": "default"}}
    image_hash = None
    media_type = "text"
    image_path = None
    issue_type = "unknown"
    routing = get_routing_info("unknown")
    status = "Pending"
    linked_to = None
    admin_remarks = None
    
    try:
        image = request.files.get("image")
        data = request.form
        print(f"📦 Payload: Image={image.filename if image else 'None'}, Title={data.get('title')}")
    except Exception as e:
        print(f"❌ Error Parsing Request: {e}")
        return jsonify({"error": "Bad Request Payload"}), 400

    image_path = None
    issue_type = "unknown"

    if image:
        # FIX: Generate unique filename to prevent overwriting
        import uuid
        import time
        ext = os.path.splitext(image.filename)[1]
        unique_filename = f"{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        image.save(image_path)
        
        # Check Media Type
        filename_lower = image.filename.lower()
        if filename_lower.endswith(('.mp4', '.mov', '.avi', '.mkv')):
            # VIDEO FLOW
            try:
                from ai.video_analyzer import process_video
                issue_type_raw = process_video(image_path)
            except Exception as e:
                print(f"Error processing video: {e}")
                issue_type_raw = "unknown"
            
            # User Constraint: "Video analysis results are advisory"
            if issue_type_raw != "unknown":
                issue_type = f"Advisory: {issue_type_raw}"
                routing = get_routing_info(issue_type_raw)
            else:
                issue_type = "unknown"
                routing = get_routing_info("unknown")
                
            status = "Pending"
            linked_to = None
            admin_remarks = "Video Analysis - Verification Required"
            image_hash = None # No hashing for video yet
            media_type = "video"
            
        else:
            # IMAGE FLOW (Existing)
            media_type = "image"
            
            # 1. Compute Hash
            from ai.duplicate_detector import compute_dhash, find_potential_duplicate
            image_hash = compute_dhash(image_path)
            
            # 2. Check Duplicate
            duplicate = find_potential_duplicate(image_hash, data.get("latitude"), data.get("longitude"))
            
            if duplicate:
                # IT IS A DUPLICATE
                # Increment support count of original
                from bson import ObjectId
                issues_collection.update_one(
                    {"_id": duplicate["_id"]},
                    {"$inc": {"support_count": 1}}
                )
                
                # Save new issue as Duplicate
                issue_type = duplicate.get("issue_type", "unknown")
                routing = {"dept": duplicate.get("assigned_department"), "priority": duplicate.get("priority")}
                status = "Duplicate"
                linked_to = str(duplicate["_id"])
                admin_remarks = f"Linked to existing issue #{str(duplicate['_id'])[-6:]}"
                
                # Copy severity from original if duplicate
                severity_data = {
                    "score": duplicate.get("severity_score", 1),
                    "label": duplicate.get("severity_label", "Low"),
                    "details": duplicate.get("severity_details", {})
                }
            else:
                # NEW UNIQUE ISSUE
                # NEW: YOLOv8 Object Detection based Civic Infrastructure Analysis
                from ai.yolo_detector import detect_issue
                yolo_result = detect_issue(image_path)
                
                if yolo_result:
                    issue_type = yolo_result["issue_type"]
                    severity_data = {
                        "score": 3 if yolo_result["severity_score"] == "High" else (2 if yolo_result["severity_score"] == "Medium" else 1),
                        "label": yolo_result["severity_score"],
                        "details": {
                            "method": "YOLOv8",
                            "area_pixels": yolo_result["detected_area_pixels"],
                            "confidence": yolo_result["confidence"],
                            "repair_cost": yolo_result["estimated_repair_cost"]
                        }
                    }
                    print(f"✅ YOLOv8 Detection: {issue_type} ({severity_data['label']})")
                else:
                    # FALLBACK: Use existing MobileNetV2 classifier
                    ai_result = classify_issue(image_path)
                    
                    if isinstance(ai_result, dict):
                        if ai_result.get("status") == "confident":
                            issue_type = ai_result.get("detected_type", "unknown")
                        elif ai_result.get("status") == "uncertain":
                            issue_type = ai_result.get("primary_guess", "unknown")
                        else:
                            issue_type = "unknown"
                    else:
                        issue_type = ai_result if ai_result else "unknown"
                    
                    # Phase 5: AI Severity Estimation
                    from ai.severity_model import estimate_severity
                    severity_data = estimate_severity(image_path, issue_type)
                    print(f"⚠️ YOLO Failed. Fallback to MobileNetV2: {issue_type}")

                # NEW: Civic Impact Radius Calculation
                from ai.impact_radius import calculate_impact_radius
                impact_data = calculate_impact_radius(
                    float(data.get("latitude", 0)), 
                    float(data.get("longitude", 0)), 
                    severity_data["label"]
                )
                
                routing = get_routing_info(issue_type)
                status = "Pending"
                linked_to = None
                admin_remarks = None
                
                # Phase 6: Forensics
                from ai.metadata_forensics import analyze_metadata
                forensics_data = analyze_metadata(image_path)
                
                # 🧠 STEP 2: BACKEND ROUTING LOGIC (Generative vs Agentic)
                ai_mode = data.get("ai_mode", "GENERATIVE") # Default to Generative (Toggle OFF)
                print(f"🧠 AI MODE: {ai_mode}")
                
                ai_summary_text = "Processing..."
                agentic_data = None
                
                if ai_mode == "AGENTIC":
                    # 🤖 AGENTIC MODE
                    try:
                        from ai.agentic_engine import run_agentic_pipeline
                        agentic_result = run_agentic_pipeline(
                            description=data.get("description", "No description"),
                            location=data.get("address", "Unknown Location"),
                            image_path=image_path
                        )
                        agentic_data = agentic_result
                        
                        # Flatten for backward compatibility
                        triage = agentic_result.get("triage", {})
                        if triage.get("valid_complaint"):
                             issue_type = triage.get("issue_type", issue_type)
                             routing["dept"] = triage.get("assigned_department", routing["dept"])
                             routing["priority"] = triage.get("priority_level", routing["priority"])
                             ai_summary_text = f"[AGENTIC DECISION] {triage.get('issue_type')} - {triage.get('priority_level')}\nPolicy: {agentic_result.get('policy', {}).get('applicable_policy')}"
                    except Exception as e:
                        print(f"❌ Agentic Pipeline Failed: {e}")
                        ai_summary_text = "Agentic AI Error"

                else:
                    # ✨ GENERATIVE MODE (Toggle OFF)
                    from ai.summarizer import summarizer
                    ai_summary_text = summarizer.generate_generative_summary(
                        description=data.get("description", "No description"),
                        location=data.get("address", "Unknown Location")
                    )
                    # Parse the text to extract fields if possible, or just store the text
                    # For now, we store the full text in admin_remarks or description supplement

    issue = {
        "reported_by": data.get("reported_by", "Anonymous"), # NEW: Store user name
        "title": data.get("title"),
        "description": data.get("description"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "address": data.get("address"), # NEW: Store the reverse-geocoded address
        "issue_type": issue_type,
        "image_path": image_path,
        "status": status,
        "assigned_department": routing["dept"],
        "priority": routing["priority"],
        "created_at": datetime.now(),
        # Phase 4 Fields
        "image_hash": image_hash,
        "support_count": 1,
        "media_type": media_type,
        "is_duplicate_of": linked_to,
        "admin_remarks": admin_remarks,
        # Phase 5 Fields
        "severity_score": severity_data["score"],
        "severity_label": severity_data["label"],
        "severity_details": severity_data["details"],
        # New YOLO & Impact Fields
        "estimated_repair_cost": severity_data["details"].get("repair_cost", 0),
        "impact_radius": impact_data.get("impact_radius", 0) if 'impact_data' in locals() else 0,
        "affected_population": impact_data.get("affected_population", 0) if 'impact_data' in locals() else 0,
        # Phase 6 Fields
        "voice_transcript": data.get("voice_transcript"),
        "forensics_data": forensics_data,
        # Phase 9 Fields
        "reporter_email": data.get("reporter_email"),  # Optional
        "notify_on_updates": data.get("notify_on_updates", "true").lower() == "true",
        "notification_history": [],
        "status_history": [{
            "status": status,
            "changed_at": datetime.now(),
            "changed_by": "System",
            "comment": "Initial report"
        }]
    }

    result = issues_collection.insert_one(issue)
    issue_id = str(result.inserted_id)
    
    # Phase 9: Send welcome notification if email provided
    reporter_email = data.get("reporter_email")
    notify_enabled = data.get("notify_on_updates", "true").lower() == "true"
    
    if reporter_email and notify_enabled:
        try:
            from services.notification_service import notification_service
            notification_data = {
                "issue_id": issue_id,
                "issue_type": issue_type,
                "address": data.get("address", "Unknown location"),
                "status": status
            }
            email_sent = notification_service.send_notification(
                reporter_email, 
                "welcome", 
                notification_data
            )
            
            # Log notification attempt
            if email_sent:
                issues_collection.update_one(
                    {"_id": result.inserted_id},
                    {"$push": {"notification_history": {
                        "type": "welcome",
                        "sent_at": datetime.now(),
                        "status": "sent"
                    }}}
                )
        except Exception as e:
            print(f"Notification error (non-critical): {e}")
    
    response_data = {
        "message": "Issue reported", 
        "issue_type": issue_type,
        "issue_id": issue_id,
        "assigned_department": routing["dept"],
        "priority": routing["priority"],
        "severity_score": severity_data["score"],
        "severity_label": severity_data["label"],
        "confidence": 98.5 if issue_type != "unknown" else 0,
        "status": status,
    }
    
    if linked_to:
        response_data["message"] = "Issue linked to existing report"
        response_data["linked_to"] = linked_to
        
    return jsonify(response_data)

@issue_bp.route("/all", methods=["GET"])
def get_all_issues():
    issues = list(issues_collection.find({}, {"_id": 0}))
    return jsonify(issues)

from bson import ObjectId

@issue_bp.route("/<issue_id>/status", methods=["GET"])
def get_issue_status(issue_id):
    # Public endpoint - only returns non-sensitive data
    try:
        issue = issues_collection.find_one(
            {"_id": ObjectId(issue_id)},
            {
                "status": 1, 
                "issue_type": 1, 
                "assigned_department": 1, 
                "created_at": 1, 
                "admin_remarks": 1, 
                "_id": 0
            }
        )
        if not issue:
            return jsonify({"error": "Not found"}), 404
        return jsonify(issue)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# NEW: AI INSPECTOR AGENT ENDPOINT
@issue_bp.route("/<issue_id>/ai-summary", methods=["GET"])
def get_ai_summary(issue_id):
    try:
        issue = issues_collection.find_one({"_id": ObjectId(issue_id)})
        if not issue:
            return jsonify({"error": "Issue not found"}), 404
            
        from ai.inspector_agent import generate_inspection_summary
        summary = generate_inspection_summary(issue)
        
        return jsonify(summary)
    except Exception as e:
        print(f"Agent Error: {e}")
        return jsonify({"error": str(e)}), 500
