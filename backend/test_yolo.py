"""End-to-end verification of the custom civic YOLOv8 model."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ai.yolo_detector as yd

model = yd._get_model()
print("Model loaded:", model is not None, "| custom flag:", yd.USING_CUSTOM)
print("Classes:", model.names)
print("-" * 70)

from ai.yolo_detector import detect_issue

images = sorted(glob.glob("uploads/*.jpg")) + sorted(glob.glob("uploads/*.png"))
hits = 0
for img in images:
    name = os.path.basename(img)
    r = detect_issue(img)
    if r:
        hits += 1
        print(
            f"{name}: {r['issue_type']} | sev={r['severity_score']} | "
            f"conf={r['confidence']} | area={r['area_ratio'] * 100:.1f}% | "
            f"boxes={r['num_detections']} | cost=Rs{r['estimated_repair_cost']}"
        )
    else:
        print(f"{name}: no detection -> falls back to MobileNetV2")

print("-" * 70)
print(f"Detected on {hits}/{len(images)} images")
