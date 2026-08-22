"""
Phase 4 - Self-Training Priority Model
Learns what makes an issue urgent from THIS city's own history.
Falls back to transparent heuristics until enough data exists (MIN_SAMPLES).
"""

import os
from datetime import datetime

import joblib

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False

_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(_DIR, "priority_model.pkl")
META_PATH = os.path.join(_DIR, "priority_model_meta.json")

MIN_SAMPLES = 100
RETRAIN_DELTA = 50  # retrain once this many new labelled issues accumulate

KNOWN_TYPES = ["pothole", "garbage", "water_leak", "drainage",
               "streetlight", "sidewalk_damage"]
SEV_MAP = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def _features(issue):
    sev = issue.get("severity_score")
    if isinstance(sev, (int, float)):
        sev_n = float(sev)
    else:
        sev_n = SEV_MAP.get(str(issue.get("severity_label") or "").title(), 2) * 2.5
    t = str(issue.get("issue_type") or "")
    return [
        sev_n,
        min(int(issue.get("support_count") or 1), 50),
        1 if t in KNOWN_TYPES else 0,
        *[1 if t == k else 0 for k in KNOWN_TYPES],
    ]


def _heuristic(issue):
    """Transparent fallback scoring, 0-100."""
    sev = issue.get("severity_score")
    score = float(sev) * 8 if isinstance(sev, (int, float)) else \
        SEV_MAP.get(str(issue.get("severity_label") or "").title(), 2) * 20
    score += min(int(issue.get("support_count") or 1), 10) * 3   # community weight
    label = str(issue.get("severity_label") or "").title()
    if label == "Critical":
        score += 15
    return int(max(0, min(100, score)))


def _load_meta():
    import json
    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            return json.load(f)
    return None


def train_priority_model(issues_collection, force=False):
    """
    Train on this city's own history: features -> admin-assigned priority.
    Returns meta dict on success, None when insufficient data.
    """
    if not SKLEARN_OK or not NUMPY_OK:
        return None

    docs = list(issues_collection.find(
        {"priority": {"$in": ["high", "medium", "low", "High", "Medium", "Low"]}},
        {"priority": 1, "issue_type": 1, "severity_score": 1,
         "severity_label": 1, "support_count": 1}
    ))
    if len(docs) < MIN_SAMPLES and not force:
        return None

    X = np.array([_features(d) for d in docs])
    y = [str(d["priority"]).lower() for d in docs]

    if len(set(y)) < 2:
        return None

    model = make_pipeline(
        StandardScaler(),
        GradientBoostingClassifier(n_estimators=120, max_depth=3, random_state=42),
    )
    model.fit(X, y)

    acc = float(model.score(X, y))  # in-sample sanity metric
    meta = {
        "trained_at": datetime.utcnow().isoformat(),
        "samples": len(docs),
        "classes": sorted(list(set(y))),
        "train_accuracy": round(acc, 3),
        "min_samples": MIN_SAMPLES,
    }
    joblib.dump(model, MODEL_PATH)
    with open(META_PATH, "w") as f:
        import json
        json.dump(meta, f, indent=2)

    print(f"[priority_model] trained on {len(docs)} issues "
          f"(classes={meta['classes']}, in-sample acc={acc:.0%})")
    return meta


def get_priority_score(issue, issues_collection=None):
    """
    Score one issue 0-100. Uses the learned model when available and fresh;
    otherwise transparent heuristics. Auto-retrains when enough new data lands.
    """
    meta = _load_meta()

    if issues_collection is not None and SKLEARN_OK:
        try:
            labelled = issues_collection.count_documents(
                {"priority": {"$exists": True, "$ne": None}})
            if (meta is None and labelled >= MIN_SAMPLES) or (
                    meta and labelled - meta["samples"] >= RETRAIN_DELTA):
                meta = train_priority_model(issues_collection)
        except Exception as e:
            print(f"[priority_model] auto-train check failed: {e}")

    if meta is not None and os.path.exists(MODEL_PATH) and SKLEARN_OK and NUMPY_OK:
        try:
            model = joblib.load(MODEL_PATH)
            probs = model.predict_proba(np.array([_features(issue)]))[0]
            classes = list(model.classes_)
            p_high = probs[classes.index("high")] if "high" in classes else 0.0
            p_med = probs[classes.index("medium")] if "medium" in classes else 0.0
            ml_score = int(round((p_high * 100 + p_med * 45)))
            return {
                "score": max(1, min(100, ml_score)),
                "label": ("High" if ml_score >= 60 else
                          "Medium" if ml_score >= 30 else "Low"),
                "source": "ml_model",
                "model_samples": meta["samples"],
            }
        except Exception as e:
            print(f"[priority_model] inference failed, using heuristic: {e}")

    h = _heuristic(issue)
    return {
        "score": h,
        "label": ("High" if h >= 60 else "Medium" if h >= 30 else "Low"),
        "source": "heuristic_fallback",
    }


def model_status():
    """For the dashboard: is the learned brain active yet?"""
    meta = _load_meta()
    return {
        "active": meta is not None,
        **(meta or {"reason": f"needs >= {MIN_SAMPLES} labelled issues to train"}),
    }
