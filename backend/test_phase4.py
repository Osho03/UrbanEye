"""Phase 4 end-to-end test: seed -> hotspots -> patterns -> priority model."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import issues_collection  # noqa: E402

# 1. SEED (idempotent-ish)
seeded = issues_collection.count_documents({"source": "demo_seed"})
if seeded < 200:
    import subprocess
    print("Seeding demo history...")
    r = subprocess.run(
        [sys.executable, "seed_demo_data.py", "--force"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        capture_output=True, text=True,
    )
    print(r.stdout.strip()[-300:] or r.stderr.strip()[-300:])
else:
    print(f"Demo data already present ({seeded} docs) - skipping seed")

print("=" * 70)

# 2. DBSCAN HOTSPOTS
from ai.hotspot_engine import detect_hotspots  # noqa: E402
issues = list(issues_collection.find(
    {"status": {"$in": ["Pending", "Assigned", "In Progress"]}},
    {"latitude": 1, "longitude": 1, "issue_type": 1, "severity_label": 1},
))
hotspots = detect_hotspots(issues, radius=50, min_count=3)
print(f"\nHOTSPOTS: {len(hotspots)} found")
for h in hotspots[:4]:
    print(f"  {h['cluster_id']}: {h['count']} issues | dominant={h['dominant_type']} "
          f"| {h['recommendation']} | center={h['center']['lat']:.4f},{h['center']['lon']:.4f}")

print("=" * 70)

# 3. SEASONAL PATTERNS
from ai.seasonal_mining import mine_patterns  # noqa: E402
all_issues = list(issues_collection.find({}, {"issue_type": 1, "created_at": 1}))
patterns = mine_patterns(all_issues)
print(f"\nPATTERNS ({patterns.get('status')}): analyzed={patterns.get('total_analyzed')}")
for s in patterns.get("spikes", [])[:5]:
    print(f"  SPIKE {s['issue_type']} in {s['month']}: {s['count']} vs baseline {s['baseline']} (+{s['uplift_pct']}%)")
for rec in patterns.get("recommendations", [])[:3]:
    print(f"  REC: {rec}")

print("=" * 70)

# 4. PRIORITY MODEL
from ai.priority_model import train_priority_model, get_priority_score, model_status  # noqa: E402
meta = train_priority_model(issues_collection)
status = model_status()
print(f"\nPRIORITY MODEL active={status.get('active')} "
      f"samples={status.get('samples')} acc={status.get('train_accuracy')}")
demo_issue = {"issue_type": "pothole", "severity_score": 8, "support_count": 12,
              "severity_label": "High"}
score = get_priority_score(demo_issue, issues_collection)
print(f"Sample scoring: pothole/sev8/support12 -> {score}")
