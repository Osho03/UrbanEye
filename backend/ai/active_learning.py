"""
Active-learning review queue - the human half of the self-teaching loop.

ai/auto_retrain.py can only learn from photos that are on disk AND labelled.
Citizen uploads give us the first but arrive carrying the model's own guess as
the label, so training on them unattended just teaches the model to repeat
itself. This module decides which uploads a human is most useful for, and
turns their verdict into real training data.

Scoring - what makes a photo worth a reviewer's time:
    uncertainty  1.0 when the detector refused to assert a class at all
                 1 - confidence otherwise  (0.61 confidence -> 0.39)
    rarity       1 - (images already collected for that class / fullest class)
                 so a doubtful pothole (10 images) outranks a doubtful piece of
                 garbage (20 images) - the queue repairs the imbalance that is
                 actually capping accuracy
    priority     0.7 * uncertainty + RARITY_WEIGHT * rarity

Reviews (POST /api/admin/review-queue/<issue_id>):
    confirm   detector was right, label stands
    relabel   admin named the true class; issue_type is corrected and the
              photo is copied into ai/dataset/<class>/ at once
    reject    not a usable civic photo (blurred, irrelevant, a video frame) -
              never enters the training set
    skip      leave it in the queue, change nothing

Accepted boxes are exported to ai/yolo_dataset/ in YOLO format. That file is
the missing ingredient for detector retraining: ai/dataset/ carries class
folders but no box geometry, which is why YOLOv8 could not join the
auto-retrain loop. Reviewing supplies the geometry with no manual drawing.

A box is only ever exported when the accepted label matches the class the box
was drawn around. Relabelling a drainage box to "pothole" would otherwise bake
the detector's existing confusion straight into the new ground truth.
"""

import os
from datetime import datetime

from ai.auto_retrain import (CLASSES, DATASET_DIR, IMG_EXT, _downscale_copy,
                             _normalise_type)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_DIR = os.path.join(BASE_DIR, "yolo_dataset")
YOLO_IMAGES = os.path.join(YOLO_DIR, "images")
YOLO_LABELS = os.path.join(YOLO_DIR, "labels")

# Class order must match the civic_yolov8 weights; see ai.yolo_detector.CLASS_MAP.
YOLO_CLASS_IDS = {
    "garbage": 0,
    "pothole": 1,
    "water_leak": 2,
    "streetlight": 3,
    "drainage": 4,
    "sidewalk_damage": 5,
}

RARITY_WEIGHT = float(os.getenv("UR_RARITY_WEIGHT", "0.30"))
SCAN_FACTOR = 20
SCAN_MIN = 200

# Same cwd-relative folder routes/issue.py writes to, so the paths stored in
# image_path resolve identically here.
UPLOAD_DIR = os.getenv("UR_UPLOAD_DIR", "uploads")

ACTIONS = ("confirm", "relabel", "reject", "skip")


# ---------------------------------------------------------------------------
# Dataset awareness
# ---------------------------------------------------------------------------

def class_counts(dataset_dir=DATASET_DIR):
    """How many training images we already hold per class."""
    counts = {}
    for cls in CLASSES:
        d = os.path.join(dataset_dir, cls)
        counts[cls] = (sum(1 for f in os.listdir(d)
                           if f.lower().endswith(IMG_EXT))
                       if os.path.isdir(d) else 0)
    return counts


def _mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_doc(doc, counts):
    """
    Rank one issue document. Returns (priority, detail) where detail carries
    the two components so the UI can show WHY a photo surfaced.
    """
    issue_type = _normalise_type(doc.get("issue_type"))
    if issue_type not in CLASSES:
        issue_type = "unknown"

    if issue_type == "unknown":
        uncertainty = 1.0
    else:
        try:
            conf = float(doc.get("detection_confidence"))
        except (TypeError, ValueError):
            conf = 0.5
        uncertainty = round(1.0 - min(max(conf, 0.0), 1.0), 4)

    fullest = max(counts.values()) if counts else 0
    if issue_type == "unknown":
        # No class to be rare about - stay neutral so genuinely doubtful
        # labelled photos can still outrank an endless tie of unknowns.
        rarity = round(_mean(1.0 - (c / fullest) for c in counts.values())
                       if fullest else 0.0, 4)
    else:
        have = counts.get(issue_type, 0)
        rarity = round(1.0 - (have / fullest), 4) if fullest else 0.0

    priority = round(min(1.0, (1.0 - RARITY_WEIGHT) * uncertainty
                         + RARITY_WEIGHT * rarity), 4)
    return priority, {
        "issue_type": issue_type,
        "uncertainty": uncertainty,
        "rarity": rarity,
        "priority": priority,
        "confidence": doc.get("detection_confidence"),
    }


def _public(doc, detail):
    from bson import ObjectId
    detections = doc.get("ml_detections") or []
    return {
        "issue_id": str(doc.get("_id") or ""),
        "title": doc.get("title"),
        "address": doc.get("address"),
        "status": doc.get("status"),
        "image_path": (doc.get("image_path") or "").replace("\\", "/"),
        "detected_image": (doc.get("detected_image") or "").replace("\\", "/")
                           if doc.get("detected_image") else None,
        "created_at": doc.get("created_at").isoformat()
                      if hasattr(doc.get("created_at"), "isoformat")
                      else None,
        "detections": [{
            "issue_type": d.get("issue_type"),
            "confidence": d.get("confidence"),
            "bounding_box": d.get("bounding_box"),
        } for d in detections if isinstance(d, dict)],
        **detail,
    }


def build_queue(issues_collection, limit=20):
    """
    Rank unreviewed photo uploads by how much a human review would help.
    Never raises - a broken queue must not take the API down.
    """
    limit = max(1, min(int(limit or 20), 100))
    counts = class_counts()

    scan = max(limit * SCAN_FACTOR, SCAN_MIN)
    query = {
        "image_path": {"$nin": [None, ""]},
        "media_type": {"$ne": "video"},
        "ml_review": {"$exists": False},
    }
    projection = {
        "issue_type": 1, "image_path": 1, "detected_image": 1,
        "detection_confidence": 1, "ml_detections": 1, "created_at": 1,
        "title": 1, "address": 1, "status": 1,
    }

    try:
        docs = list(issues_collection.find(query, projection)
                    .sort("created_at", -1).limit(scan))
    except Exception as e:
        return {"success": False, "message": f"queue query failed: {e}",
                "items": [], "stats": {}}

    scored = []
    for doc in docs:
        if doc.get("is_duplicate_of"):
            continue
        priority, detail = score_doc(doc, counts)
        scored.append((priority, doc.get("created_at"), _public(doc, detail)))

    # Newest first among equal scores so the queue still moves over time.
    scored.sort(key=lambda t: (t[0], t[1] or datetime.min), reverse=True)

    reviewed = 0
    try:
        reviewed = issues_collection.count_documents(
            {"ml_review": {"$exists": True}})
    except Exception:
        pass

    return {
        "success": True,
        "items": [item for _, _, item in scored[:limit]],
        "scanned": len(docs),
        "pending": len(scored),
        "stats": {
            "classes": CLASSES,
            "class_counts": counts,
            "dataset_images": sum(counts.values()),
            "reviewed": reviewed,
            "rarity_weight": RARITY_WEIGHT,
            "scanned": len(docs),
        },
    }


# ---------------------------------------------------------------------------
# Applying a human decision
# ---------------------------------------------------------------------------

def _pick_box(detections, label):
    """Top-confidence box whose class equals the accepted label, else None."""
    for det in sorted((d for d in (detections or [])
                       if isinstance(d, dict)
                       and d.get("issue_type") == label
                       and d.get("bounding_box")),
                      key=lambda d: d.get("confidence") or 0.0, reverse=True):
        return det
    return None


def _export_yolo_sample(issue_id, image_path, label, box):
    """
    Write one YOLO-format sample: <class_id> <xc> <yc> <w> <h>, all normalised.
    The image is copied (downscaled) so the detector trains on a standard
    input. Returns the label filename, or None when the box is unusable.
    """
    if box is None or label not in YOLO_CLASS_IDS:
        return None
    x1, y1, x2, y2 = box
    if min(x1, y1, x2, y2) < 0:
        return None
    try:
        from PIL import Image
        os.makedirs(YOLO_IMAGES, exist_ok=True)
        os.makedirs(YOLO_LABELS, exist_ok=True)
        img_name = f"{issue_id}.jpg"
        dest = os.path.join(YOLO_IMAGES, img_name)
        if not os.path.exists(dest):
            _downscale_copy(image_path, dest)
        with Image.open(dest) as im:
            w, h = im.size
        if not w or not h:
            return None
        line = (f"{YOLO_CLASS_IDS[label]} "
                f"{(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} "
                f"{abs(x2 - x1) / w:.6f} {abs(y2 - y1) / h:.6f}")
        label_path = os.path.join(YOLO_LABELS, img_name.replace(".jpg", ".txt"))
        with open(label_path, "w") as f:
            f.write(line + "\n")
        return os.path.basename(label_path)
    except Exception as e:
        print(f"[active_learning] YOLO export failed for {issue_id}: {e}")
        return None


def apply_label(issues_collection, issue_id, action, label=None,
                reviewer="admin", keep_box=False):
    """
    Record a reviewer's verdict and, when the label is usable, put the photo
    into the training set immediately (not on the next scheduled sweep).
    """
    from bson import ObjectId
    from bson.errors import InvalidId

    action = (action or "").strip().lower()
    if action not in ACTIONS:
        return {"success": False,
                "message": f"action must be one of {', '.join(ACTIONS)}"}

    try:
        oid = ObjectId(issue_id)
    except (InvalidId, TypeError):
        return {"success": False, "message": "malformed issue id",
                "code": 400}

    doc = issues_collection.find_one({"_id": oid})
    if not doc:
        return {"success": False, "message": "issue not found", "code": 404}

    if action == "skip":
        return {"success": True, "action": action, "trained": False,
                "message": "left in the queue"}

    previous = _normalise_type(doc.get("issue_type"))
    image_path = doc.get("image_path")

    if action == "reject":
        issues_collection.update_one(
            {"_id": oid},
            {"$set": {"ml_review": {
                "action": "reject", "reviewer": reviewer,
                "reviewed_at": datetime.now(), "previous_type": previous,
                "trained": False}}})
        return {"success": True, "action": action, "trained": False,
                "label": previous,
                "message": "marked unusable - excluded from training"}

    label = (label or (previous if action == "confirm" else "")).strip().lower()
    if label not in CLASSES:
        return {"success": False, "code": 400,
                "message": f"label must be one of {', '.join(CLASSES)}"}
    if action == "confirm" and label != previous:
        return {"success": False, "code": 400,
                "message": (f"confirm keeps the detected label ({previous}); "
                            f"use relabel to set {label}")}

    trained = False
    if image_path and os.path.exists(image_path):
        os.makedirs(os.path.join(DATASET_DIR, label), exist_ok=True)
        dest = os.path.join(DATASET_DIR, label, f"{issue_id}.jpg")
        try:
            if not os.path.exists(dest):
                _downscale_copy(image_path, dest)
            trained = True
        except Exception as e:
            print(f"[active_learning] copy failed {image_path}: {e}")
    else:
        print(f"[active_learning] image missing on disk: {image_path}")

    yolo_label = None
    box_note = None
    if keep_box:
        box = _pick_box(doc.get("ml_detections"), label)
        if box is None:
            drawn = sorted({d.get("issue_type") for d
                            in (doc.get("ml_detections") or [])
                            if isinstance(d, dict)})
            box_note = (f"no {label} box was drawn for this photo"
                        + (f" (detector drew: {', '.join(filter(None, drawn))})"
                           if drawn else ""))
        else:
            yolo_label = _export_yolo_sample(issue_id, image_path, label, box)
    elif doc.get("ml_detections"):
        box_note = "box not kept (enable 'keep box' to export YOLO ground truth)"

    issues_collection.update_one(
        {"_id": oid},
        {"$set": {
            "issue_type": label,
            "ml_review": {
                "action": action, "label": label, "reviewer": reviewer,
                "reviewed_at": datetime.now(), "previous_type": previous,
                "previous_confidence": doc.get("detection_confidence"),
                "trained": trained, "yolo_label": yolo_label,
            },
        }})

    return {
        "success": True,
        "action": action,
        "label": label,
        "previous_type": previous,
        "corrected": label != previous,
        "trained": trained,
        "yolo_label": yolo_label,
        "box_note": box_note,
        "class_counts": class_counts(),
        "message": (f"{label} -> training set ({previous} was the AI guess)"
                    if label != previous
                    else f"{label} confirmed into the training set"),
    }


def queue_stats(issues_collection):
    """One-shot summary used by the Model Health card."""
    counts = class_counts()
    try:
        pending = issues_collection.count_documents({
            "image_path": {"$nin": [None, ""]},
            "media_type": {"$ne": "video"},
            "ml_review": {"$exists": False}})
        reviewed = issues_collection.count_documents(
            {"ml_review": {"$exists": True}})
    except Exception as e:
        return {"error": str(e)}
    try:
        yolo_samples = len([f for f in os.listdir(YOLO_LABELS)
                            if f.endswith(".txt")]) if os.path.isdir(YOLO_LABELS) else 0
    except OSError:
        yolo_samples = 0
    return {
        "pending_review": pending,
        "reviewed": reviewed,
        "class_counts": counts,
        "dataset_images": sum(counts.values()),
        "rarest": min(counts, key=counts.get) if counts else None,
        "yolo_labeled_boxes": yolo_samples,
    }


# ---------------------------------------------------------------------------
# Reconciling uploads/ with the database
# ---------------------------------------------------------------------------

# Rendered overlays, not original citizen photos.
_ORPHAN_SKIP_PREFIX = ("annotated_",)


def scan_orphan_uploads(issues_collection, upload_dir=UPLOAD_DIR):
    """
    Real photos sitting in uploads/ that no issue document points at.

    These are the most valuable unlabelled data in the project - they are
    genuine citizen photos - but they are invisible to both this queue and
    ai.auto_retrain.collect_from_db(), which both walk the database, not the
    filesystem. Returns the list of absolute paths.
    """
    if not os.path.isdir(upload_dir):
        return []
    try:
        referenced = set()
        for doc in issues_collection.find(
                {}, {"image_path": 1, "detected_image": 1}):
            for key in ("image_path", "detected_image"):
                value = doc.get(key)
                if value:
                    referenced.add(os.path.normcase(
                        os.path.basename(str(value).replace("\\", "/"))))
    except Exception as e:
        print(f"[active_learning] orphan scan failed: {e}")
        return []

    orphans = []
    for name in sorted(os.listdir(upload_dir)):
        if not name.lower().endswith(IMG_EXT):
            continue
        if name.startswith(_ORPHAN_SKIP_PREFIX):
            continue
        if os.path.normcase(name) in referenced:
            continue
        orphans.append(os.path.join(upload_dir, name))
    return orphans


def reconcile_orphans(issues_collection, upload_dir=UPLOAD_DIR, dry_run=True):
    """
    Register unreferenced uploads/ photos as reviewable issues labelled
    "unknown" so they enter the queue at maximum uncertainty.

    This creates issue documents, so it defaults to a dry run. The documents
    are marked ml_reconciled to stay distinguishable from real citizen reports
    in any analytics that counts issues.
    """
    orphans = scan_orphan_uploads(issues_collection, upload_dir)
    if dry_run:
        return {"success": True, "dry_run": True, "found": len(orphans),
                "sample": [os.path.basename(p) for p in orphans[:10]],
                "message": (f"{len(orphans)} photo(s) in "
                            f"{upload_dir}/ belong to no issue record")}

    now = datetime.now()
    created = 0
    for path in orphans:
        name = os.path.basename(path)
        try:
            stat = os.path.getmtime(path)
        except OSError:
            continue
        issues_collection.insert_one({
            "title": f"[Uncategorised upload] {name}",
            "description": "Photo found on disk with no matching issue "
                           "record. Needs a human label.",
            "address": None,
            "latitude": None,
            "longitude": None,
            "issue_type": "unknown",
            "image_path": path.replace("\\", "/"),
            "detected_image": None,
            "detection_confidence": 0.0,
            "ml_detections": [],
            "ml_reconciled": True,
            "status": "Pending",
            "media_type": "image",
            "created_at": datetime.fromtimestamp(stat),
        })
        created += 1
    print(f"[active_learning] reconciled {created} orphaned upload(s)")
    return {"success": True, "dry_run": False, "found": len(orphans),
            "created": created,
            "message": f"queued {created} photo(s) for review"}
