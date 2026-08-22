"""
Phase 4 - Demo History Seeder
Generates ~300 realistic synthetic issues across 12 months so the analytics
features (hotspots, seasonal spikes, priority training) have data to chew on.

Safe by design: refuses to run when real data exists unless --force is passed.
All seeded docs carry source='demo_seed' for easy identification/removal.
"""

import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "backend")

from config import issues_collection  # noqa: E402

# Bengaluru-ish geography: 8 ward centers with natural clustering
WARDS = [
    (12.9716, 77.5946), (12.9784, 77.6408), (12.9352, 77.6245),
    (12.9698, 77.7500), (12.9121, 77.6446), (13.0298, 77.5400),
    (12.9081, 77.5677), (13.0104, 77.5568),
]

# Tight trouble-spots: same-street clusters DBSCAN should discover
HOTSPOT_CENTERS = [
    (12.9750, 77.6060), (12.9420, 77.6185), (13.0055, 77.5520),
]

TYPE_WEIGHTS = {
    "pothole": 30, "garbage": 28, "water_leak": 14,
    "drainage": 10, "streetlight": 10, "sidewalk_damage": 8,
}

DEPT_MAP = {
    "pothole": "Road Department", "sidewalk_damage": "Road Department",
    "garbage": "Sanitation Department",
    "water_leak": "Water Board", "drainage": "Water Board",
    "streetlight": "Electricity Department",
}

SEV_LABELS = ["Low", "Medium", "High"]


def pick_type(month):
    # Monsoon (Jun-Aug => months 6,7,8) triples pothole & water issues
    weights = dict(TYPE_WEIGHTS)
    if month in (6, 7, 8):
        weights["pothole"] *= 3
        weights["water_leak"] *= 2
        weights["drainage"] *= 2
    population = list(weights.keys())
    return random.choices(population, weights=list(weights.values()))[0]


def main(force=False):
    existing = issues_collection.count_documents({})
    if existing > 50 and not force:
        print(f"Refusing to seed: {existing} documents look like REAL data.")
        print("Pass --force if you are sure.")
        return
    if force:
        removed = issues_collection.delete_many({"source": "demo_seed"})
        if removed.deleted_count:
            print(f"Cleared {removed.deleted_count} previous demo docs.")

    now = datetime.now()
    docs = []

    for i in range(300):
        days_ago = random.randint(0, 364)
        created = now - timedelta(days=days_ago)

        # 35% land in tight street-corner clusters -> real DBSCAN hotspots;
        # the rest spread loosely across wards.
        if random.random() < 0.35:
            w_lat, w_lon = random.choice(HOTSPOT_CENTERS)
            lat = round(w_lat + random.gauss(0, 0.00012), 6)   # ~13 m jitter
            lon = round(w_lon + random.gauss(0, 0.00012), 6)
        else:
            w_lat, w_lon = random.choice(WARDS)
            lat = round(w_lat + random.gauss(0, 0.0035), 6)
            lon = round(w_lon + random.gauss(0, 0.0035), 6)

        # Hotspot issues skew recent & high-severity (unresolved trouble spots)
        if (w_lat, w_lon) in HOTSPOT_CENTERS and lat != w_lat:
            pass

        issue_type = pick_type(created.month)

        # Age drives status: old stuff got fixed
        if days_ago > 90:
            status = "Resolved" if random.random() < 0.88 else "Assigned"
        elif days_ago > 25:
            status = random.choices(
                ["Resolved", "In Progress", "Assigned", "Pending"],
                weights=[45, 20, 20, 15])[0]
        else:
            status = random.choices(
                ["Pending", "Assigned", "In Progress", "Resolved"],
                weights=[45, 30, 20, 5])[0]

        sev_label = random.choices(SEV_LABELS, weights=[30, 45, 25])[0]
        sev_score = {"Low": random.randint(2, 3),
                     "Medium": random.randint(4, 6),
                     "High": random.randint(7, 9)}[sev_label]

        priority = ("high" if sev_score >= 7 else
                    "medium" if sev_score >= 4 else "low")
        if status == "Resolved":
            priority = "low" if random.random() < 0.75 else priority

        support = max(1, int(random.expovariate(1 / 3)) + (3 if days_ago < 60 else 0))

        docs.append({
            "source": "demo_seed",
            "title": f"[Demo] {issue_type.replace('_', ' ').title()} report",
            "description": f"Seeded historical {issue_type} complaint for analytics.",
            "reported_by": random.choice(["Demo Citizen A", "Demo Citizen B", "Anonymous"]),
            "issue_type": issue_type,
            "latitude": str(lat),
            "longitude": str(lon),
            "address": "Seeded demo location",
            "image_path": None,
            "detected_image": None,
            "media_type": "image",
            "status": status,
            "priority": priority,
            "assigned_department": DEPT_MAP.get(issue_type, "General Maintenance"),
            "severity_score": sev_score,
            "severity_label": sev_label,
            "support_count": support,
            "created_at": created,
            "status_history": [{"status": status, "changed_at": created,
                                "changed_by": "Seeder", "comment": "seed"}],
        })

    result = issues_collection.insert_many(docs)
    print(f"Seeded {len(result.inserted_ids)} demo issues "
          f"(monsoon pothole bias included).")
    print("Remove anytime with:")
    print('  db.issues.deleteMany({source: "demo_seed"})')


if __name__ == "__main__":
    main(force="--force" in sys.argv)
