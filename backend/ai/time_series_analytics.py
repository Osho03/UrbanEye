"""Real-time time-series analytics for the live admin dashboard.

Pure-Python, dependency-light trend bucketing + Poisson-normal anomaly
detection. Works on mixed data types because some legacy reports store
``created_at`` as an RFC-822 string while newer ones store a real datetime.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _to_dt(value):
    """Best-effort datetime parsing: datetime, ISO-8601, RFC-822 or pandas."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        s = value.strip()
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            try:
                dt = parsedate_to_datetime(s)
            except (TypeError, ValueError):
                try:
                    import pandas as pd
                    ts = pd.to_datetime(s, errors="coerce")
                    if pd.isna(ts):
                        return None
                    dt = ts.to_pydatetime()
                except Exception:
                    return None
    else:
        return None

    # Normalise timezone-aware timestamps to naive local for clean comparisons.
    if dt.tzinfo is not None:
        try:
            dt = dt.astimezone().replace(tzinfo=None)
        except Exception:
            return None
    return dt


def _norm_type(raw):
    if isinstance(raw, dict):
        return raw.get("detected_type") or raw.get("primary_guess") or "unknown"
    s = str(raw or "unknown").strip().lower()
    return s or "unknown"


def build_trends(docs, days=30, granularity="daily", now=None):
    """Bucket issue counts by day or hour across the last ``days``.

    Returns a JSON-safe series dict aligned so every label has a value,
    making the front-end charts trivially renderable.
    """
    now = now or datetime.now()
    cut = now - timedelta(days=days)
    granularity = granularity if granularity in ("daily", "hourly") else "daily"

    counts = defaultdict(int)      # (bucket, type) -> count
    totals = defaultdict(int)      # bucket -> total
    for doc in docs:
        ts = _to_dt(doc.get("created_at"))
        if ts is None or ts < cut or ts > now:
            continue
        key = ts.strftime("%Y-%m-%d") if granularity == "daily" \
            else ts.strftime("%Y-%m-%dT%H:00")
        t = _norm_type(doc.get("issue_type"))
        counts[(key, t)] += 1
        totals[key] += 1

    labels = []
    if granularity == "daily":
        cur = datetime(cut.year, cut.month, cut.day)
        while cur <= now:
            labels.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=1)
    else:
        cur = cut.replace(minute=0, second=0, microsecond=0)
        while cur <= now:
            labels.append(cur.strftime("%Y-%m-%dT%H:00"))
            cur += timedelta(hours=1)

    if not labels:
        return {"status": "no_data", "labels": [], "by_type": {},
                "per_day_total": [], "generated_at": now.isoformat()}

    types = sorted({t for (_, t) in counts})
    by_type = {t: [counts.get((lb, t), 0) for lb in labels] for t in types}
    series = [totals.get(lb, 0) for lb in labels]

    busiest = labels[max(range(len(series)), key=lambda i: series[i])]
    peak_type = max(by_type, key=lambda t: sum(by_type[t]) or -1) if by_type else None

    return {
        "status": "ok",
        "granularity": granularity,
        "days": days,
        "labels": labels,
        "month_labels": MONTH_NAMES,
        "by_type": by_type,
        "per_day_total": series,
        "total_reported": sum(series),
        "busiest": busiest,
        "peak_type": peak_type,
        "generated_at": now.isoformat(),
    }


def detect_anomalies(docs, window_hours=24, history_hours=168, min_actual=3,
                     uplift_threshold=150, z_threshold=2.0, now=None):
    """Flag issue-types whose recent report rate is abnormal.

    A Poisson-normal approximation: the recent window (default 24h) is compared
    against the expected count derived from the preceding history window
    (default 7 days). ``z = (actual - expected) / sqrt(expected)``.

    Returns a JSON-safe dict with a list of anomalies + a plain-language summary.
    """
    now = now or datetime.now()
    recent_start = now - timedelta(hours=window_hours)
    hist_start = now - timedelta(hours=window_hours + history_hours)

    recent = defaultdict(int)   # type -> count in last 24h
    history = defaultdict(int)  # (type, hour_index) -> count
    for doc in docs:
        ts = _to_dt(doc.get("created_at"))
        if ts is None or ts > now:
            continue
        t = _norm_type(doc.get("issue_type"))
        if ts >= recent_start:
            recent[t] += 1
        elif ts >= hist_start:
            history[(t, (ts.year, ts.month, ts.day, ts.hour))] += 1

    anomalies = []
    for t in sorted(set(recent) | {k[0] for k in history}):
        actual = recent[t]
        hist_total = sum(c for (kt, _), c in history.items() if kt == t)
        if actual < min_actual:
            continue
        expected = hist_total * (window_hours / history_hours)
        if expected <= 0:
            uplift_pct = 999
            z_score = min(actual, 99)  # strong signal, no baseline
        else:
            uplift_pct = (actual - expected) / expected * 100
            z_score = (actual - expected) / (expected ** 0.5)

        anomaly = (uplift_pct >= uplift_threshold and z_score >= 1.0) or \
            z_score >= 3.0
        if not anomaly:
            continue

        if z_score >= 4 or uplift_pct >= 400:
            severity = "Critical"
        elif z_score >= 2.5 or uplift_pct >= 200:
            severity = "High"
        else:
            severity = "Medium"

        message = (
            f"{t.replace('_', ' ')} reports {int(uplift_pct):+d}% in the last "
            f"{window_hours}h ({actual} vs {expected:.1f} expected)."
            if expected > 0 else
            f"New {t.replace('_', ' ')} activity detected in the last "
            f"{window_hours}h ({actual} reports, zero baseline)."
        )
        anomalies.append({
            "issue_type": t,
            "actual": actual,
            "expected": round(expected, 2),
            "uplift_pct": int(round(uplift_pct)),
            "z_score": round(z_score, 2),
            "severity": severity,
            "message": message,
        })

    anomalies.sort(
        key=lambda a: a["z_score"] if a["expected"] else 99, reverse=True
    )

    return {
        "status": "ok",
        "window_hours": window_hours,
        "baseline_hours": history_hours,
        "anomalies": anomalies,
        "summary": (
            f"{len(anomalies)} issue type(s) showing abnormal activity in "
            f"the last {window_hours}h."
            if anomalies else
            "No abnormal activity detected in the last 24h."
        ),
        "generated_at": now.isoformat(),
    }