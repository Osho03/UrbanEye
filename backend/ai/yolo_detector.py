try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

import os
import json

# Load YOLOv8 Nano model lazily - skip on cloud if not available
MODEL_PATH = "yolov8n.pt"
model = None

def _get_model():
    global model
    if model is None and YOLO_AVAILABLE and os.path.exists(MODEL_PATH):
        try:
            model = YOLO(MODEL_PATH)
        except Exception as e:
            print(f"⚠️ Could not load YOLO model: {e}")
    return model


def detect_issue(image_path):
    """
    Detect civic issues using YOLOv8.
    Predicts issue type, severity, and repair cost.
    
    Args:
        image_path (str): Path to the uploaded image
        
    Returns:
        dict: Detection results including issue_type, bounding_box, area, severity, and cost.
    """
    yolo_model = _get_model()
    if not yolo_model:
        return None  # YOLO not available on this server
    try:
        results = yolo_model.predict(image_path, conf=0.25)
        
        if not results or len(results[0].boxes) == 0:
            return None
            
        # Get the primary detection (highest confidence)
        box = results[0].boxes[0]
        class_id = int(box.cls[0])
        class_name = model.names[class_id]
        
        # Calculate bounding box coordinates and area
        # box.xyxy returns [x1, y1, x2, y2]
        coords = box.xyxy[0].tolist()
        x1, y1, x2, y2 = coords
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        # Mapping COCO/Generic classes to UrbanEye classes (Fallback logic)
        # Note: In a real scenario, the model would be trained on pothole, garbage, etc.
        issue_mapping = {
            "pothole": "pothole",
            "garbage": "garbage",
            "water_leak": "water_leak",
            "streetlight": "streetlight"
        }
        
        # If the detected class isn't in our mapping, we label it as 'other'
        issue_type = class_name if class_name in issue_mapping else "infrastructure_anomaly"
        
        # Severity Logic based on bounding box area
        if area < 5000:
            severity = "Low"
            cost = 500
        elif area < 15000:
            severity = "Medium"
            cost = 1500
        else:
            severity = "High"
            cost = 3000
            
        return {
            "issue_type": issue_type,
            "bounding_box": coords,
            "detected_area_pixels": round(area, 2),
            "severity_score": severity,
            "estimated_repair_cost": cost,
            "confidence": float(box.conf[0])
        }
        
    except Exception as e:
        print(f"❌ YOLO Detection Error: {e}")
        return None
