"""Free Google Gemini vision fallback for UrbanEye detection.

When the trained YOLOv8 model finds nothing in a photo, this module asks
Gemini (free tier) to name what is actually there, so the app still shows
a class name instead of "unknown".

It is a pure backup path: if google.generativeai is not installed or no
GEMINI_API_KEY is set, every function returns None and the detection
pipeline behaves exactly as before.
"""

import json
import os
import re
import time

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Must stay aligned with yolo_onnx.CLASS_NAMES
CLASS_NAMES = ["garbage", "pothole", "water_leak", "streetlight", "drainage", "sidewalk_damage"]

# Vision-capable models, tried in order of preference.
_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

_model = None
_model_index = 0
_configured = False

_PROMPT = """You are UrbanEye's civic infrastructure classifier. Look at the photo.
Only these 6 labels are allowed:
garbage, pothole, water_leak, streetlight, drainage, sidewalk_damage

Decide which single label best matches the damage/object in the photo.
Reply with ONLY one JSON object, no extra words:
{"issue_type": "<one of the 6 labels or unknown>", "confidence": <0.0 to 1.0>}
If the photo shows none of these civic issue types, return "unknown" with confidence 0.0."""


def _setup():
    global _configured
    if not GENAI_AVAILABLE:
        return False
    if not _configured:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return False
        genai.configure(api_key=api_key)
        _configured = True
    return True


def _get_model():
    global _model, _model_index
    if _model is not None:
        return _model
    if not _setup():
        return None
    for i in range(_model_index, len(_MODELS)):
        try:
            m = genai.GenerativeModel(_MODELS[i])
            _model = m
            _model_index = i
            print(f"[gemini_vision] using model {_MODELS[i]}")
            return m
        except Exception as e:
            print(f"[gemini_vision] model {_MODELS[i]} unavailable: {e}")
    return None


def _parse_response(text):
    """Extract {issue_type, confidence} from Gemini's reply."""
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    data = None
    try:
        data = json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                data = None
    if not isinstance(data, dict):
        return None

    issue_type = str(data.get("issue_type", "unknown")).strip().lower()
    if issue_type not in CLASS_NAMES:
        issue_type = "unknown"
    try:
        conf = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    return {"issue_type": issue_type, "confidence": round(conf, 3)}


def classify_image(image_path, timeout_seconds=25):
    """Name the civic issue in a photo using free Gemini vision.

    Returns {"issue_type", "confidence", "source", "model", "latency_ms"}
    when a civic class is recognized, {"issue_type": "unknown", ...} when
    Gemini sees nothing useful, or None on any failure / no API key.
    """
    if not os.path.exists(image_path) or not PIL_AVAILABLE:
        return None
    model = _get_model()
    if model is None:
        return None

    try:
        img = PILImage.open(image_path).convert("RGB")
    except Exception as e:
        print(f"[gemini_vision] image read error: {e}")
        return None

    start = time.time()
    try:
        resp = model.generate_content(
            [_PROMPT, img],
            request_options={"timeout": timeout_seconds},
        )
        text = (resp.text or "").strip()
    except Exception as e:
        print(f"[gemini_vision] API error: {e}")
        return None
    latency_ms = round((time.time() - start) * 1000)

    parsed = _parse_response(text)
    if parsed is None:
        print(f"[gemini_vision] unparseable response: {text[:160]!r}")
        return None

    parsed["source"] = "gemini_vision"
    parsed["model"] = model.model_name
    parsed["latency_ms"] = latency_ms
    print(f"[gemini_vision] {parsed['issue_type']} conf={parsed['confidence']} "
          f"({latency_ms}ms)")
    return parsed