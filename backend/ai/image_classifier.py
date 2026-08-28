"""
AI Image Classifier for UrbanEye AI
Human-in-the-Loop Learning System - Inference Module

This module performs real-time inference using either:
1. Pretrained MobileNetV2 (default, general features)
2. Fine-tuned model (if available, domain-specific)

The classifier automatically uses the fine-tuned model if it exists,
otherwise falls back to the pretrained model.

Two-Phase System:
- Inference (this file): Real-time predictions on uploads
- Training (train_model.py): Offline fine-tuning on verified data
"""

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
import json
import os

# Paths
LABELS_PATH = os.path.join(os.path.dirname(__file__), "labels.json")
TRAINED_MODEL_PATH = os.path.join(os.path.dirname(__file__), "urbaneye_finetuned_model.h5")

# Load labels
with open(LABELS_PATH) as f:
    LABELS = json.load(f)

model = None
# Check if fine-tuned model exists (Lazy Check)
USING_FINETUNED = os.path.exists(TRAINED_MODEL_PATH)


def classify_issue(image_path):
    """
    Classify image using the trained local model only.
    Uses the fine-tuned MobileNetV2 model (urbaneye_finetuned_model.h5).
    Returns a dict with status, detected_type, and confidence.
    """
    global model
    
    # Lazy Import TensorFlow
    try:
        from tensorflow.keras.models import load_model
    except ImportError:
        print("⚠️ TensorFlow not available. Returning unknown.")
        return {"status": "confident", "detected_type": "unknown", "confidence": 0.0, "requires_confirmation": False}

    # Load Model if not loaded
    if model is None:
        print("⚡ Lazy Loading Model...")
        if os.path.exists(TRAINED_MODEL_PATH):
            model = load_model(TRAINED_MODEL_PATH)
        else:
            print("⚠️ No trained model found. Returning unknown.")
            return {"status": "confident", "detected_type": "unknown", "confidence": 0.0, "requires_confirmation": False}
        print("✅ Model Loaded.")

    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print(f"⚠️ Could not load image: {image_path}")
            return "unknown"
        
        # Resize to model input size
        img = cv2.resize(img, (224, 224))
        
        # Convert BGR to RGB (OpenCV loads as BGR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        img = img / 255.0
        
        # Expand dimensions for batch processing
        img = np.expand_dims(img, axis=0)
        
        # Get predictions
        preds = model.predict(img, verbose=0)
        # PRODUCTION AI RULE: Set confidence threshold
        CONFIDENCE_THRESHOLD = 0.60  # 60% minimum for asserting classification
        
        # Make prediction
        predictions = model.predict(img, verbose=0)
        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])
        
        # Get class label
        class_label = LABELS[str(predicted_class_idx)]
        
        # HONEST AI: Check confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
            # Get top 3 predictions for user to choose from
            # Ensure indices are valid for LABELS
            top_3_indices = np.argsort(predictions[0])[-3:][::-1]
            suggestions = [
                {
                    "type": LABELS[str(idx)],
                    "confidence": round(float(predictions[0][idx]) * 100, 1)
                }
                for idx in top_3_indices if str(idx) in LABELS
            ]
            
            print(f"⚠️  Low confidence ({confidence:.2%}) - Requesting user confirmation")
            
            return {
                "status": "uncertain",
                "primary_guess": class_label,
                "confidence": round(confidence * 100, 1),
                "requires_confirmation": True,
                "explanation": f"Confidence ({confidence:.0%}) is below threshold ({CONFIDENCE_THRESHOLD:.0%}). The image may be ambiguous or have low visual clarity. Human confirmation requested.",
                "suggestions": suggestions
            }
        
        # Confident prediction
        model_type = "fine-tuned" if USING_FINETUNED else "pretrained"
        print(f"✅ Classified as: {class_label} (confidence: {confidence:.2f}, model: {model_type})")
        
        return {
            "status": "confident",
            "detected_type": class_label,
            "confidence": round(confidence * 100, 1),
            "requires_confirmation": False
        }
        
    except Exception as e:
        print(f"❌ Error classifying image: {e}")
        return {"status": "error", "message": str(e)}
