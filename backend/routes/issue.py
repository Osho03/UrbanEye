import os
import numpy as np
from flask import Blueprint, request, jsonify
from config import issues_collection
from datetime import datetime

issue_bp = Blueprint("issue", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# When YOLO returns a label but its confidence is below this, ask the free
# Gemini vision verifier to double-check so the app never shows a
# confidently-wrong problem name.
GEMINI_VERIFY_CONF = 0.55


def _pyval(v):
    """Recursively convert numpy scalars to native Python types (MongoDB-safe)."""
    if v is None or isinstance(v, (bool, str, bytes)):
        return v
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, dict):
        return {k: _pyval(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_pyval(x) for x in v]
    return v

@issue_bp.route("/report", methods=["POST"])
def report_issue():
    print("➡️ Received Report Request") # DEBUG LOG
    
    # Lazy imports
    from routes.routing import get_routing_info
    try:
        from ai.image_classifier import classify_issue
    except Exception as e:
        print(f"Warning: image_classifier not available: {e}")
        def classify_issue(path): return "unknown"

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
    detection_confidence = 0.0
    
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
        # .jfif is a JPEG that ultralytics/OpenCV cannot open -> save as .jpg
        if ext.lower() in ("", ".jfif"):
            ext = ".jpg"
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
            detected_image = None  # Phase 3: annotated YOLO overlay path
            
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
                    detection_confidence = yolo_result.get("confidence", 0.0)

                    # Free Gemini VERIFIER: when YOLO is unsure of its own
                    # label (below GEMINI_VERIFY_CONF), ask Gemini to look at
                    # the photo too. Gemini only overrides when it is MORE
                    # confident, so a confident low false-positive never wins.
                    if detection_confidence < GEMINI_VERIFY_CONF:
                        try:
                            from ai.gemini_vision import classify_image
                            gem = classify_image(image_path)
                        except Exception as e:
                            print(f"⚠️ Gemini verifier unavailable: {e}")
                            gem = None
                        if gem and gem.get("issue_type") not in (None, "unknown"):
                            g_conf = float(gem.get("confidence", 0.0))
                            if gem["issue_type"] == issue_type:
                                print(f"✅ Gemini verifier agrees with YOLO: {issue_type}")
                            elif g_conf > detection_confidence:
                                print(f"✅ Gemini verifier override: "
                                      f"{issue_type} ({detection_confidence:.2f}) -> "
                                      f"{gem['issue_type']} ({g_conf:.2f})")
                                issue_type = gem["issue_type"]
                                detection_confidence = round(g_conf, 3)

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

                    # Phase 3: Visual Detection Layer - paint boxes on the proof
                    from ai.annotate import annotate_detection
                    detected_image = annotate_detection(image_path, yolo_result)
                    if detected_image:
                        severity_data["details"]["annotated"] = True
                        print(f"🖼️ Annotated evidence saved: {detected_image}")
                else:
                    # YOLO found nothing. The trained YOLO model stays the
                    # primary detector; as a free backup, ask Gemini vision
                    # to name what it sees so the app still shows a class
                    # instead of "unknown". Skipped when no GEMINI_API_KEY
                    # is configured, keeping the old behaviour unchanged.
                    try:
                        from ai.gemini_vision import classify_image
                        gemini_result = classify_image(image_path)
                    except Exception as e:
                        print(f"⚠️ Gemini vision unavailable: {e}")
                        gemini_result = None

                    if gemini_result and gemini_result.get("issue_type") not in (None, "unknown"):
                        issue_type = gemini_result["issue_type"]
                        detection_confidence = float(gemini_result.get("confidence", 0.5))
                        print(f"✅ Gemini Vision fallback: {issue_type} (conf={detection_confidence})")

                        # Phase 5: AI Severity Estimation (with the real type)
                        from ai.severity_model import estimate_severity
                        severity_data = estimate_severity(image_path, issue_type)
                        severity_data["details"]["method"] = "gemini_fallback"
                    else:
                        print("⚠️ YOLO found no civic issue - reporting unknown")
                        issue_type = "unknown"
                        detection_confidence = 0.0

                        # Phase 5: AI Severity Estimation
                        from ai.severity_model import estimate_severity
                        severity_data = estimate_severity(image_path, issue_type)

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
                             # Only use agentic text label if the vision model found nothing.
                             # The trained YOLO/MobileNet detection is authoritative.
                             triage_type = triage.get("issue_type")
                             if not issue_type or issue_type == "unknown":
                                 issue_type = triage_type or issue_type
                             routing["dept"] = triage.get("assigned_department", routing["dept"])
                             routing["priority"] = triage.get("priority_level", routing["priority"])
                             ai_summary_text = f"[AGENTIC DECISION] {triage_type} - {triage.get('priority_level')}\nPolicy: {agentic_result.get('policy', {}).get('applicable_policy')}"
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
        "detected_image": detected_image if media_type == "image" else None,  # Phase 3
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

    issue = _pyval(issue)

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
        "confidence": detection_confidence,
        "status": status,
    }
    
    if linked_to:
        response_data["message"] = "Issue linked to existing report"
        response_data["linked_to"] = linked_to
        
    return jsonify(_pyval(response_data))

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
