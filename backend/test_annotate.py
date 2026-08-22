"""Phase 3 verification: detect -> annotate -> validate output."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.yolo_detector import detect_issue
from ai.annotate import annotate_detection

import cv2

target = None
for f in sorted(os.listdir("uploads")):
    if f.endswith(".jpg"):
        r = detect_issue(os.path.join("uploads", f))
        if r and r["confidence"] > 0.5:
            target = (os.path.join("uploads", f), r)
            break

assert target, "No confident detection found among uploads - cannot test annotation."

path, result = target
print(f"Source : {path}")
print(f"Detect : {result['issue_type']} conf={result['confidence']} sev={result['severity_score']}")

out = annotate_detection(path, result)
print(f"Output : {out}")
assert out and os.path.exists(out), "annotate_detection returned no file"

img = cv2.imread(out)
assert img is not None, "Annotated file unreadable"
print(f"Valid  : {img.shape[1]}x{img.shape[0]} px annotated image OK")
