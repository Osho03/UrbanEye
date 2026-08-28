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

# Custom civic-trained weights take priority; stock COCO weights are fallback.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CANDIDATES = [
    os.path.join(_BASE_DIR, "models", "civic_yolov8.pt"),
    os.path.join(_BASE_DIR, "civic_yolov8.pt"),
]
STOCK_MODEL_PATH = os.path.join(os.getcwd(), "yolov8n.pt")

model = None
USING_CUSTOM = False


def _resolve_weights():
    for p in MODEL_CANDIDATES:
        if os.path.exists(p):
            return p, True
    if os.path.exists(STOCK_MODEL_PATH):
        return STOCK_MODEL_PATH, False
    return None, False


def _get_model():
    global model, USING_CUSTOM
    if model is None and YOLO_AVAILABLE:
        # Keep native thread count low to limit memory on low-RAM hosts (Render free).
        try:
            import torch
            torch.set_num_threads(1)
        except Exception:
            pass
        weights, custom = _resolve_weights()
        if weights:
            try:
                model = YOLO(weights)
                USING_CUSTOM = custom
                src = "CUSTOM civic_yolov8" if custom else "STOCK yolov8n (COCO)"
                print(f"[yolo_detector] Loaded {src} from {weights}")
            except Exception as e:
                print(f"[yolo_detector] Could not load YOLO model: {e}")
    return model


# Maps trained class names to canonical UrbanEye issue types.
# civic_v2 model outputs: garbage, pothole, water_leak, streetlight, drainage, sidewalk_damage
CLASS_MAP = {
    "pothole": "pothole",
    "garbage": "garbage",
    "trash": "garbage",
    "waste": "garbage",
    "litter": "garbage",
    "drainage": "drainage",
    "drain": "drainage",
    "drain hole": "drainage",
    "sewer": "drainage",
    "manhole": "drainage",
    "water_leak": "water_leak",
    "pipe leak": "water_leak",
    "water leak": "water_leak",
    "leak": "water_leak",
    "streetlight": "streetlight",
    "street_light": "streetlight",
    "street-lamp": "streetlight",
    "street light": "streetlight",
    "lightpost": "streetlight",
    "sidewalk_damage": "sidewalk_damage",
    "sidewalk": "sidewalk_damage",
    "edge break": "sidewalk_damage",
    "crack": "sidewalk_damage",
    "patch": "sidewalk_damage",
    "0": "garbage",
    "1": "pothole",
    "2": "water_leak",
    "3": "streetlight",
    "4": "drainage",
    "5": "sidewalk_damage",
    "class0": "garbage",
    "class1": "pothole",
    "class2": "water_leak",
    "class3": "streetlight",
    "class4": "drainage",
    "class5": "sidewalk_damage",
}

# Severity by area ratio (box area / image area) - resolution independent.
SEVERITY_BANDS = [
    (0.02, "Low", 500),
    (0.08, "Medium", 1500),
    (float("inf"), "High", 3000),
]


def _map_class(raw_name):
    key = str(raw_name).strip().lower()
    if key in CLASS_MAP:
        return CLASS_MAP[key]
    for token, issue_type in (
        ("poth", "pothole"), ("garb", "garbage"), ("trash", "garbage"),
        ("waste", "garbage"), ("litter", "garbage"),
        ("leak", "water_leak"), ("water", "water_leak"),
        ("drain", "drainage"), ("sewer", "drainage"), ("manhole", "drainage"),
        ("street", "streetlight"), ("lamp", "streetlight"), ("light", "streetlight"),
        ("sidewalk", "sidewalk_damage"), ("crack", "sidewalk_damage"),
        ("patch", "sidewalk_damage"),
    ):
        if token in key:
            return issue_type
    return None


def _severity_for(ratio, num_detections):
    for limit, label, cost in SEVERITY_BANDS:
        if ratio < limit:
            # Multiple detections in one frame indicate a wider problem.
            extra = min(num_detections - 1, 5) * 200
            return label, cost + max(extra, 0)
    return "Low", 500


def detect_issue(image_path):
    """
    Detect civic issues using YOLOv8.

    With CUSTOM civic_yolov8.pt weights:
      - Real civic classes (pothole, garbage, drainage, ...)
      - Severity derived from damaged-area ratio of the frame
      - Repair cost scaled by severity and detection count

    Without custom weights (stock COCO yolov8n.pt):
      - Honest fallback: returns None unless a mapped class appears,
        letting routes/issue.py fall through to the MobileNetV2 classifier.

    Returns None when ultralytics/weights are unavailable or nothing maps
    to a known civic issue type.
    """
    yolo_model = _get_model()
    if not yolo_model or not CV2_AVAILABLE:
        return None

    try:
        results = yolo_model.predict(image_path, conf=0.25, verbose=False)

        if not results or len(results[0].boxes) == 0:
            return None

        result = results[0]
        img_h, img_w = result.orig_shape
        img_area = float(img_h * img_w)

        detections = []
        for box in result.boxes:
            raw_name = yolo_model.names[int(box.cls[0])]
            issue_type = _map_class(raw_name) if USING_CUSTOM else CLASS_MAP.get(str(raw_name).strip().lower())
            if issue_type is None:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            area = max(x2 - x1, 1) * max(y2 - y1, 1)
            detections.append({
                "issue_type": issue_type,
                "bounding_box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "area_pixels": round(area, 2),
                "area_ratio": round(area / img_area, 4),
                "confidence": round(float(box.conf[0]), 3),
            })

        if not detections:
            return None

        # Primary detection = highest confidence among civic classes.
        primary = max(detections, key=lambda d: d["confidence"])
        severity, cost = _severity_for(primary["area_ratio"], len(detections))

        return {
            "issue_type": primary["issue_type"],
            "bounding_box": primary["bounding_box"],
            "detected_area_pixels": primary["area_pixels"],
            "area_ratio": primary["area_ratio"],
            "num_detections": len(detections),
            "detections": detections,
            "severity_score": severity,
            "estimated_repair_cost": cost,
            "confidence": primary["confidence"],
            "model_source": "custom" if USING_CUSTOM else "coco_fallback",
        }

    except Exception as e:
        print(f"[yolo_detector] Detection error: {e}")
        return None
