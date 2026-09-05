"""Lightweight YOLOv8 inference for the trained civic model.

Runs civic_yolov8.onnx through onnxruntime (CPU) with NO torch and NO
ultralytics import, so the backend fits in low-RAM hosts (Render free =
512 MB). Preprocessing mirrors ultralytics: letterbox to 640, /255,
BGR->RGB, CHW; then cxcywh decode, confidence threshold, NMS, and rescale
boxes back to the original image coordinates.
"""

import os

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_BASE_DIR, "models", "civic_yolov8.onnx")

CLASS_NAMES = ["garbage", "pothole", "water_leak", "streetlight", "drainage", "sidewalk_damage"]

_session = None
_CONF = 0.25
_IOU = 0.45

# Per-class confidence floors. The nano model is weak at night/low-light
# scenes, so junk boxes (a dark road patch misread as pothole, a dim blob
# misread as streetlight) were passing the old 0.25 floor and topping the
# highest-confidence pick. These floors reject most false positives while
# keeping the true positives seen in the real dataset.
_CLASS_CONF = {
    0: 0.30,  # garbage
    1: 0.32,  # pothole
    2: 0.30,  # water_leak
    3: 0.30,  # streetlight
    4: 0.30,  # drainage
    5: 0.30,  # sidewalk_damage
}


def available():
    return ONNX_AVAILABLE and CV2_AVAILABLE and os.path.exists(_MODEL_PATH)


def load():
    global _session
    if _session is None and available():
        _session = ort.InferenceSession(_MODEL_PATH, providers=["CPUExecutionProvider"])
    return _session


def _letterbox(im, new_size=640):
    h, w = im.shape[:2]
    r = min(new_size / w, new_size / h)
    nw, nh = round(w * r), round(h * r)
    dw, dh = (new_size - nw) / 2, (new_size - nh) / 2
    im = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right,
                            cv2.BORDER_CONSTANT, value=(114, 114, 114))
    return im, r, dw, dh


def _box_iou(a, b):
    x1 = np.maximum(a[:, 0], b[:, 0])
    y1 = np.maximum(a[:, 1], b[:, 1])
    x2 = np.minimum(a[:, 2], b[:, 2])
    y2 = np.minimum(a[:, 3], b[:, 3])
    inter = np.maximum(x2 - x1, 0) * np.maximum(y2 - y1, 0)
    area_a = np.maximum(a[:, 2] - a[:, 0], 0) * np.maximum(a[:, 3] - a[:, 1], 0)
    area_b = np.maximum(b[:, 2] - b[:, 0], 0) * np.maximum(b[:, 3] - b[:, 1], 0)
    return inter / np.maximum(area_a + area_b - inter, 1e-9)


def _nms(xyxy, confs, iou_thres):
    keep = []
    order = confs.argsort()[::-1]
    while order.size:
        i = order[0]
        keep.append(int(i))
        if order.size == 1:
            break
        iou = _box_iou(xyxy[i][None, :], xyxy[order[1:]])
        order = order[1:][iou < iou_thres]
    return keep


def predict(image_path):
    """Run YOLOv8 ONNX on an image.

    Returns {"width": w, "height": h, "detections": [{class_id, name,
    confidence, box (xyxy in original pixels)}]} or None on any failure.
    """
    sess = load()
    if sess is None:
        return None

    im0 = cv2.imread(image_path)
    if im0 is None:
        return None

    ih, iw = im0.shape[:2]
    im, r, dw, dh = _letterbox(im0)
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    blob = np.transpose(rgb.astype(np.float32) / 255.0, (2, 0, 1))[None, ...]

    try:
        out = sess.run(None, {sess.get_inputs()[0].name: blob})[0]
    except Exception as e:
        print(f"[yolo_onnx] Inference error: {e}")
        return None

    preds = out[0]
    boxes = preds[:4]          # cx, cy, w, h  (letterboxed pixels)
    scores = preds[4:]         # per-class scores, shape (nc, 8400)
    confs = scores.max(axis=0)
    cls_ids = scores.argmax(axis=0)
    thr = np.array([_CLASS_CONF.get(c, _CONF) for c in range(scores.shape[0])])
    mask = confs >= thr[cls_ids]
    if not mask.any():
        return None

    xyxy = np.stack([
        boxes[0] - boxes[2] / 2,
        boxes[1] - boxes[3] / 2,
        boxes[0] + boxes[2] / 2,
        boxes[1] + boxes[3] / 2,
    ], axis=1)
    candidates = mask.nonzero()[0]

    detections = []
    for keep_i in _nms(xyxy[candidates], confs[candidates], _IOU):
        idx = candidates[keep_i]
        x1 = (xyxy[idx, 0] - dw) / r
        y1 = (xyxy[idx, 1] - dh) / r
        x2 = (xyxy[idx, 2] - dw) / r
        y2 = (xyxy[idx, 3] - dh) / r
        x1 = max(0.0, min(x1, iw))
        y1 = max(0.0, min(y1, ih))
        x2 = max(0.0, min(x2, iw))
        y2 = max(0.0, min(y2, ih))
        cid = int(cls_ids[idx])
        detections.append({
            "class_id": cid,
            "name": CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else str(cid),
            "confidence": round(float(confs[idx]), 3),
            "box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
        })

    if not detections:
        return None
    return {"width": iw, "height": ih, "detections": detections}