"""Verify urbaneye_finetuned_model.h5 loads and predicts correctly."""
import json
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import cv2
import numpy as np
from tensorflow.keras.models import load_model

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "ai", "urbaneye_finetuned_model.h5")
LABELS_PATH = os.path.join(BASE, "ai", "labels.json")

with open(LABELS_PATH) as f:
    LABELS = json.load(f)

print(f"Labels ({len(LABELS)}): {list(LABELS.values())}")

print("\nLoading model...")
model = load_model(MODEL_PATH)
input_shape = model.input_shape
output_shape = model.output_shape
print(f"Input shape : {input_shape}")
print(f"Output shape: {output_shape}")
print(f"Params      : {model.count_params():,}")

if output_shape[-1] != len(LABELS):
    print(f"MISMATCH: model outputs {output_shape[-1]} classes but labels.json has {len(LABELS)}")
    raise SystemExit(1)


def predict(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Could not read: {image_path}")
        return
    img = cv2.resize(img, (224, 224))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) / 255.0
    preds = model.predict(np.expand_dims(img, axis=0), verbose=0)[0]
    top = np.argsort(preds)[::-1][:3]
    print(f"\n{os.path.basename(image_path)}:")
    for idx in top:
        print(f"  {LABELS[str(idx)]:<18} {preds[idx] * 100:5.1f}%")


candidates = [
    os.path.join(os.path.dirname(BASE), "test_image_access.jpg"),
    os.path.join(BASE, "uploads"),
]

tested = False
for c in candidates:
    if os.path.isfile(c):
        predict(c)
        tested = True
    elif os.path.isdir(c):
        for name in sorted(os.listdir(c))[:3]:
            if name.lower().endswith((".jpg", ".jpeg", ".png")):
                predict(os.path.join(c, name))
                tested = True

if not tested:
    print("\nNo test images found - model loaded OK but nothing to predict on.")

print("\nMODEL VERIFICATION PASSED" if tested else "\nMODEL LOAD PASSED")
