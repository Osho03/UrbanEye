"""
Phase 4 - DBSCAN Hotspot Engine
Replaces the greedy fixed-radius loop in predictive_analytics.py.

DBSCAN with the haversine metric finds hotspots of ANY shape and marks
lonely issues as noise instead of forcing them into fake clusters.
Drop-in compatible output shape with the old detect_hotspots().
"""

import math

import numpy as np

try:
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def _recommendation(dominant_type, count):
    recommendation = "Inspect Area"
    if dominant_type == "pothole" and count >= 5:
        recommendation = "Critical: Road Resurfacing Recommended"
    elif dominant_type == "pothole":
        recommendation = "Patchwork Required"
    elif dominant_type == "garbage":
        recommendation = "Increase Sanitation Schedule"
    elif dominant_type == "streetlight":
        recommendation = "Grid Failure Check"
    elif dominant_type == "water_leak":
        recommendation = "Pipeline Leak Survey"
    return recommendation


def _norm_type(raw):
    if isinstance(raw, dict):
        return raw.get("detected_type") or raw.get("primary_guess") or "unknown"
    return str(raw or "unknown")


def detect_hotspots(issues, radius=50, min_count=3):
    """
    Cluster civic issues geographically using DBSCAN.

    Args:
        issues: list of dicts with latitude/longitude (+ optional issue_type,
                severity_label, _id)
        radius: neighborhood size in meters
        min_count: minimum issues to form a hotspot (DBSCAN min_samples)

    Returns:
        list of hotspot dicts sorted by severity of the problem (count desc).
        Shape-compatible with predictive_analytics.detect_hotspots().
    """
    valid = []
    for issue in issues:
        try:
            lat = float(issue["latitude"])
            lon = float(issue["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            continue
        valid.append((issue, lat, lon))

    if len(valid) < min_count:
        return []

    coords = np.radians([[lat, lon] for _, lat, lon in valid])

    if SKLEARN_AVAILABLE:
        eps_radians = radius / 6371000.0  # Earth radius -> meters to radians
        labels = DBSCAN(
            eps=eps_radians,
            min_samples=min_count,
            metric="haversine",
        ).fit_predict(coords)
    else:
        # Fallback: old greedy behaviour if sklearn is unavailable
        return _greedy_fallback(valid, radius, min_count)

    clusters = {}
    noise = 0
    for idx, label in enumerate(labels):
        if label == -1:
            noise += 1
            continue
        clusters.setdefault(int(label), []).append(idx)

    hotspots = []
    for label, member_idx in clusters.items():
        group = [valid[i][0] for i in member_idx]
        lats = [valid[i][1] for i in member_idx]
        lons = [valid[i][2] for i in member_idx]

        types = {}
        severities = {"High": 0, "Medium": 0, "Low": 0}
        ids = []
        for g in group:
            t = _norm_type(g.get("issue_type"))
            types[t] = types.get(t, 0) + 1
            sev = str(g.get("severity_label") or "").title()
            if sev in severities:
                severities[sev] += 1
            gid = g.get("_id")
            if gid is not None:
                ids.append(str(gid))

        dominant_type = max(types, key=types.get)
        count = len(group)

        hotspots.append({
            "cluster_id": f"H{label:02d}",
            "center": {
                "lat": round(sum(lats) / count, 6),
                "lon": round(sum(lons) / count, 6),
            },
            "count": count,
            "types": types,
            "dominant_type": dominant_type,
            "severity_mix": {k: v for k, v in severities.items() if v},
            "recommendation": _recommendation(dominant_type, count),
            "radius": radius,
            "issue_ids": ids[:50],  # cap payload size
        })

    hotspots.sort(key=lambda h: h["count"], reverse=True)
    print(f"[hotspot_engine] {len(hotspots)} hotspots ({noise} outlier points ignored)")
    return hotspots


def _greedy_fallback(valid, radius, min_count):
    """Legacy O(n^2) clustering used only when scikit-learn is missing."""
    def dist(a_lat, a_lon, b_lat, b_lon):
        R = 6371000
        p1, p2 = math.radians(a_lat), math.radians(b_lat)
        dp = math.radians(b_lat - a_lat)
        dl = math.radians(b_lon - a_lon)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    clusters, visited = [], set()
    for i, (iss1, la1, lo1) in enumerate(valid):
        if i in visited:
            continue
        members = [i]
        visited.add(i)
        for j in range(i + 1, len(valid)):
            if j in visited:
                continue
            if dist(la1, lo1, valid[j][1], valid[j][2]) <= radius:
                members.append(j)
                visited.add(j)
        if len(members) < min_count:
            continue
        group = [valid[k][0] for k in members]
        types = {}
        for g in group:
            t = _norm_type(g.get("issue_type"))
            types[t] = types.get(t, 0) + 1
        dominant = max(types, key=types.get)
        clusters.append({
            "cluster_id": f"G{len(clusters):02d}",
            "center": {
                "lat": round(sum(valid[k][1] for k in members) / len(members), 6),
                "lon": round(sum(valid[k][2] for k in members) / len(members), 6),
            },
            "count": len(members),
            "types": types,
            "dominant_type": dominant,
            "recommendation": _recommendation(dominant, len(members)),
            "radius": radius,
        })
    return clusters
