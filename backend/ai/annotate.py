"""
Phase 3 - Visual Detection Layer
Draws YOLO bounding boxes + labels onto uploaded photos so admins can SEE
what the model detected. Output is saved next to the original upload.
"""

import os

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# BGR colors per severity label
SEVERITY_COLORS = {
    "High": (0, 0, 255),
    "Medium": (0, 165, 255),
    "Low": (0, 200, 0),
}
DEFAULT_COLOR = (255, 120, 0)

FONT = cv2.FONT_HERSHEY_SIMPLEX if CV2_AVAILABLE else None


def _label_text(det):
    conf = det.get("confidence", 0)
    return f"{det['issue_type'].upper()} {conf * 100:.0f}%"


def annotate_detection(image_path, yolo_result):
    """
    Draw every detection from detect_issue() output onto the image.

    Returns the relative path of the annotated copy (same convention as
    image_path, e.g. 'uploads/annotated_xyz.jpg'), or None on failure.
    Never raises - callers fall back to the plain photo.
    """
    if not CV2_AVAILABLE or not yolo_result:
        return None

    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        h, w = img.shape[:2]
        thickness = max(2, int(min(w, h) / 300))
        font_scale = max(0.45, min(w, h) / 900)

        detections = yolo_result.get("detections") or [{
            "issue_type": yolo_result.get("issue_type", "issue"),
            "bounding_box": yolo_result.get("bounding_box"),
            "confidence": yolo_result.get("confidence", 0),
        }]

        for det in detections:
            box = det.get("bounding_box")
            if not box or len(box) != 4:
                continue
            x1, y1, x2, y2 = [int(round(v)) for v in box]
            # Clamp to frame
            x1, x2 = max(0, min(x1, w - 1)), max(1, min(x2, w))
            y1, y2 = max(0, min(y1, h - 1)), max(1, min(y2, h))

            severity = str(yolo_result.get("severity_score", ""))
            color = SEVERITY_COLORS.get(severity, DEFAULT_COLOR)

            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

            # Label chip above the box
            text = _label_text(det)
            (tw, th), baseline = cv2.getTextSize(text, FONT, font_scale, thickness)
            ty = y1 - baseline - 6
            if ty - th < 0:  # box touches top edge -> put chip inside
                ty = y1 + th + baseline + 6
            chip_top, chip_bottom = ty - th - 4, ty + baseline + 2
            cv2.rectangle(img, (x1, chip_top), (x1 + tw + 8, chip_bottom), color, -1)
            cv2.putText(img, text, (x1 + 4, ty), FONT, font_scale,
                        (255, 255, 255), thickness, cv2.LINE_AA)

        out_dir = os.path.dirname(image_path)
        orig_name = os.path.basename(image_path)
        name, ext = os.path.splitext(orig_name)
        out_path = os.path.join(out_dir, f"annotated_{name}{ext or '.jpg'}")

        ok = cv2.imwrite(out_path, img)
        if not ok:
            return None

        return f"{out_dir.replace(os.sep, '/')}/{os.path.basename(out_path)}"

    except Exception as e:
        print(f"[annotate] Failed to annotate {image_path}: {e}")
        return None
