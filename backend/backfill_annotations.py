"""One-shot backfill: add AI annotations to issues uploaded before Phase 3."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import issues_collection
from ai.yolo_detector import detect_issue
from ai.annotate import annotate_detection

query = {
    "detected_image": {"$exists": False},
    "image_path": {"$ne": None, "$exists": True},
}

targets = list(issues_collection.find(query))
print(f"Issues needing annotation: {len(targets)}")

done, no_detect, missing_file, failed = 0, 0, 0, 0

for issue in targets:
    rel_path = (issue.get("image_path") or "").replace("/", os.sep)
    img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)

    if not os.path.exists(img_path):
        missing_file += 1
        print(f"[skip] file missing: {issue['image_path']}")
        continue

    result = detect_issue(img_path)
    if not result:
        no_detect += 1
        continue

    annotated = annotate_detection(img_path, result)
    if not annotated:
        failed += 1
        continue

    issues_collection.update_one(
        {"_id": issue["_id"]},
        {"$set": {"detected_image": annotated}}
    )
    done += 1
    print(
        f"[ok] {issue['image_path']} -> {annotated} "
        f"({result['issue_type']} {result['confidence'] * 100:.0f}%)"
    )

print("-" * 60)
print(f"Annotated : {done}")
print(f"No detection (left as-is): {no_detect}")
print(f"File missing: {missing_file} | Failed: {failed}")
