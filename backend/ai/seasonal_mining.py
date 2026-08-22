"""
Phase 4 - Seasonal Pattern Mining
Groups historical issues by month / weekday to surface recurring patterns,
e.g. "potholes spike +240% during monsoon (June-Aug)".
"""

from collections import Counter, defaultdict

import pandas as pd

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _norm_type(raw):
    if isinstance(raw, dict):
        return raw.get("detected_type") or raw.get("primary_guess") or "unknown"
    return str(raw or "unknown")


def mine_patterns(issues, spike_factor=1.5):
    """
    Args:
        issues: list of issue dicts (created_at + issue_type required)
        spike_factor: month counts above baseline * factor count as spikes

    Returns dict with monthly_matrix, spikes, weekday_profile, recommendations.
    """
    rows = []
    for issue in issues:
        created = issue.get("created_at")
        if not created:
            continue
        ts = pd.to_datetime(created, errors="coerce")
        if pd.isna(ts):
            continue
        rows.append({
            "type": _norm_type(issue.get("issue_type")),
            "month": ts.month - 1,          # 0-11
            "weekday": ts.weekday(),        # 0=Mon
            "hour": ts.hour,
        })

    df = pd.DataFrame(rows)
    total = len(df)
    if total < 10:
        return {
            "status": "insufficient_data",
            "message": f"Only {total} dated issues; need >= 10 for pattern mining.",
            "total_analyzed": total,
        }

    types = df["type"].value_counts()
    top_types = list(types.head(6).index)

    # --- Monthly matrix per type ---
    monthly = defaultdict(lambda: [0] * 12)
    for t in top_types:
        counts = df[df["type"] == t].groupby("month").size()
        for m, c in counts.items():
            monthly[t][int(m)] = int(c)

    # --- Spike detection: month >> type's average ---
    spikes = []
    for t in top_types:
        series = monthly[t]
        active_months = [c for i, c in enumerate(series) if c > 0]
        if len(active_months) < 2:
            continue
        baseline = sum(active_months) / len(active_months)
        for m, c in enumerate(series):
            if baseline > 0 and c >= 3 and c >= baseline * spike_factor:
                spikes.append({
                    "issue_type": t,
                    "month": MONTH_NAMES[m],
                    "count": c,
                    "baseline": round(baseline, 1),
                    "uplift_pct": int(round((c / baseline - 1) * 100)),
                })
    spikes.sort(key=lambda s: s["uplift_pct"], reverse=True)

    # --- Weekday profile ---
    weekday_counts = Counter(df["weekday"].map(lambda w: WEEKDAYS[w]))
    weekday_profile = {d: int(weekday_counts.get(d, 0)) for d in WEEKDAYS}
    busiest_day = max(weekday_profile, key=weekday_profile.get)

    # --- Hour profile (reporting time) ---
    hour_counts = Counter(df["hour"])
    peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else None

    # --- Human-readable recommendations ---
    recommendations = []
    monsoon_types = {"pothole", "water_leak", "drainage"}
    for s in spikes[:4]:
        if s["issue_type"] in monsoon_types and s["month"] in ("Jun", "Jul", "Aug", "Sep"):
            recommendations.append(
                f"Pre-monsoon maintenance drive for '{s['issue_type']}' before {s['month']} "
                f"(historically +{s['uplift_pct']}%)."
            )
        elif s["issue_type"] == "garbage":
            recommendations.append(
                f"Increase sanitation pickups in {s['month']} "
                f"(garbage reports +{s['uplift_pct']}% vs average)."
            )
        else:
            recommendations.append(
                f"Staff ahead of '{s['issue_type']}' surge in {s['month']} (+{s['uplift_pct']}%)."
            )
    recommendations.append(
        f"Peak complaint inflow lands on {busiest_day}s around "
        f"{peak_hour:02d}:00 - schedule support staff accordingly."
        if peak_hour is not None else
        f"Busiest reporting day is {busiest_day}."
    )

    return {
        "status": "ok",
        "total_analyzed": total,
        "monthly_matrix": {t: monthly[t] for t in top_types},
        "month_labels": MONTH_NAMES,
        "spikes": spikes[:8],
        "weekday_profile": weekday_profile,
        "peak_report_hour": peak_hour,
        "recommendations": recommendations,
    }
