import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
const BASE_URL = API_URL.replace(/\/api$/, "");

const pct = (v) => (typeof v === "number" ? `${Math.round(v * 100)}%` : "--");

const CLASSES = [
    ["pothole", "🕳 Pothole"],
    ["garbage", "🗑 Garbage"],
    ["drainage", "🌀 Drainage"],
    ["streetlight", "💡 Streetlight"],
    ["water_leak", "💧 Water leak"],
    ["sidewalk_damage", "🧱 Sidewalk"],
];

const ReviewQueue = () => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    const [busy, setBusy] = useState(false);
    const [note, setNote] = useState(null);
    const [orphan, setOrphan] = useState(null);
    const [training, setTraining] = useState(false);

    const fetchQueue = useCallback(async () => {
        try {
            const res = await axios.get(`${API_URL}/admin/review-queue?limit=12`);
            if (res.data?.success) {
                setData(res.data);
                setError(null);
            } else {
                setError(res.data?.message || "queue unavailable");
            }
        } catch (err) {
            setError(err.message);
        }
    }, []);

    useEffect(() => {
        fetchQueue();
    }, [fetchQueue]);

    const decide = async (issueId, body) => {
        setBusy(true);
        setNote(null);
        try {
            const res = await axios.post(`${API_URL}/admin/review-queue/${issueId}`, body);
            if (res.data?.success) {
                const extra = res.data.box_note ? ` (${res.data.box_note})` : "";
                setNote({ ok: true, text: `${res.data.message}${extra}` });
                await fetchQueue();
            } else {
                setNote({ ok: false, text: res.data?.message || "review failed" });
            }
        } catch (err) {
            setNote({ ok: false, text: err.message });
        } finally {
            setBusy(false);
        }
    };

    const checkOrphans = async (commit) => {
        setBusy(true);
        setOrphan(null);
        try {
            const res = commit
                ? await axios.post(`${API_URL}/admin/ml/reconcile-uploads`)
                : await axios.get(`${API_URL}/admin/ml/reconcile-uploads`);
            setOrphan(res.data);
            if (commit && res.data?.created) await fetchQueue();
        } catch (err) {
            setOrphan({ message: err.message });
        } finally {
            setBusy(false);
        }
    };

    const retrain = async () => {
        setTraining(true);
        setNote(null);
        try {
            const res = await axios.post(`${API_URL}/admin/ml/retrain`);
            const d = res.data?.retrain;
            setNote({
                ok: d?.status === "done",
                text: d?.status === "done"
                    ? `Retrained on ${d.trained_samples} photos (${pct(d.train_accuracy)} train acc) — guard said "${d.decision?.verdict}".`
                    : `Retrain ${d?.status}: ${d?.message || "see server log"}`,
            });
        } catch (err) {
            setNote({ ok: false, text: err.message });
        } finally {
            setTraining(false);
        }
    };

    if (error) {
        return (
            <div className="card" style={{ borderLeft: "4px solid #F56565" }}>
                <h3 style={{ margin: 0 }}>Active-Learning Review Queue</h3>
                <p style={{ color: "#C53030", fontSize: "0.85rem" }}>{error}</p>
            </div>
        );
    }
    if (!data) return null;

    const counts = data.stats?.class_counts || {};
    const rarest = data.stats?.rarest;
    const fullest = Math.max(1, ...Object.values(counts));
    const items = data.items || [];

    return (
        <div className="card" style={{
            background: "linear-gradient(135deg, #fffaf0 0%, #fff 100%)",
            borderRadius: "16px",
            padding: "1.5rem",
            boxShadow: "0 4px 6px rgba(237, 137, 54, 0.1)",
            borderLeft: "4px solid #ED8936",
            marginBottom: "2rem",
        }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                <div>
                    <h3 style={{ fontSize: "0.85rem", textTransform: "uppercase", color: "#C05621", margin: 0, fontWeight: "bold" }}>
                        Active-Learning Queue · teach the model by reviewing
                    </h3>
                    <p style={{ margin: "5px 0 0", fontSize: "0.9rem", color: "#4A5568" }}>
                        <strong>{data.pending}</strong> photo(s) the AI is least sure about, most uncertain first.
                        Every review you make lands in the training set immediately.
                    </p>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button className="btn" disabled={busy} onClick={() => checkOrphans(false)}
                        style={{ background: "#DD6B20", color: "white", border: "none", borderRadius: "8px", padding: "0.6rem 1rem", fontWeight: "600", cursor: busy ? "not-allowed" : "pointer" }}>
                        🔍 Find uncategorised uploads
                    </button>
                    <button className="btn" disabled={training} onClick={retrain}
                        style={{ background: training ? "#A0AEC0" : "#2F855A", color: "white", border: "none", borderRadius: "8px", padding: "0.6rem 1rem", fontWeight: "600", cursor: training ? "not-allowed" : "pointer" }}>
                        {training ? "⚙ Training…" : "🧠 Retrain now"}
                    </button>
                </div>
            </div>

            {orphan && (
                <div style={{ marginTop: "1rem", padding: "0.85rem 1rem", borderRadius: "10px", fontSize: "0.85rem",
                    background: "rgba(221,107,32,0.08)", border: "1px solid rgba(221,107,32,0.25)", color: "#7B341E" }}>
                    <p style={{ margin: 0 }}>{orphan.message}</p>
                    {orphan.found > 0 && (
                        <button className="btn" disabled={busy} onClick={() => checkOrphans(true)}
                            style={{ marginTop: "0.6rem", background: "#DD6B20", color: "white", border: "none", borderRadius: "6px", padding: "0.4rem 0.8rem", fontWeight: "600", cursor: "pointer" }}>
                            Queue {orphan.found} photo(s) for review
                        </button>
                    )}
                </div>
            )}

            {note && (
                <p style={{ marginTop: "1rem", fontSize: "0.85rem", fontWeight: "600",
                    color: note.ok ? "#2F855A" : "#C53030" }}>{note.text}</p>
            )}

            <div style={{ marginTop: "1.25rem" }}>
                <p style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "#718096", margin: "0 0 0.5rem" }}>
                    Training set balance — thin classes surface first
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "0.6rem" }}>
                    {CLASSES.map(([cls, label]) => {
                        const n = counts[cls] || 0;
                        const thin = n < fullest * 0.75;
                        return (
                            <div key={cls} style={{ background: thin ? "rgba(221,107,32,0.10)" : "rgba(66,153,225,0.08)",
                                border: `1px solid ${thin ? "rgba(221,107,32,0.3)" : "rgba(66,153,225,0.18)"}`,
                                borderRadius: "10px", padding: "0.5rem 0.6rem" }}>
                                <p style={{ margin: 0, fontSize: "0.72rem", color: "#4A5568" }}>{label}</p>
                                <p style={{ margin: "0.1rem 0 0", fontSize: "1.05rem", fontWeight: "700",
                                    color: thin ? "#C05621" : "#2D3748" }}>
                                    {n} {thin && <span style={{ fontSize: "0.7rem" }}>· thin</span>}
                                </p>
                            </div>
                        );
                    })}
                </div>
                {rarest && <p style={{ fontSize: "0.75rem", color: "#718096", marginTop: "0.5rem" }}>
                    Weakest class: <strong>{rarest}</strong> ({counts[rarest]} photos).
                    Reviews of doubtful <strong>{rarest}</strong> photos are weighted highest.
                </p>}
            </div>

            {items.length === 0 ? (
                <p style={{ marginTop: "1.25rem", fontSize: "0.9rem", color: "#4A5568" }}>
                    Nothing waiting. Either every upload has been reviewed, or no upload has a photo on disk yet —
                    use <strong>Find uncategorised uploads</strong> above to check.
                </p>
            ) : (
                <div style={{ marginTop: "1.25rem", display: "grid", gap: "0.9rem" }}>
                    {items.map((it) => (
                        <div key={it.issue_id} style={{ display: "flex", gap: "1rem", padding: "0.85rem",
                            borderRadius: "12px", background: "rgba(255,255,255,0.6)",
                            border: "1px solid rgba(237,137,54,0.22)" }}>
                            <img
                                src={`${BASE_URL}/${it.detected_image || it.image_path}`}
                                alt={it.title || "upload"}
                                onError={(e) => { e.target.onerror = null; e.target.src = `${BASE_URL}/uploads/__missing__`; }}
                                style={{ width: "128px", height: "128px", objectFit: "cover", borderRadius: "10px",
                                    border: "1px solid rgba(0,0,0,0.08)", flexShrink: 0, background: "#EDF2F7" }}
                            />
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.4rem" }}>
                                    <p style={{ margin: 0, fontSize: "0.9rem", fontWeight: "700", color: "#2D3748" }}>
                                        AI says: {it.issue_type === "unknown"
                                            ? <span style={{ color: "#C05621" }}>unknown (refused to guess)</span>
                                            : it.issue_type}
                                        {typeof it.confidence === "number" && it.issue_type !== "unknown" &&
                                            <span style={{ fontWeight: "400", color: "#A0AEC0" }}> · {pct(it.confidence)} confident</span>}
                                    </p>
                                    <p style={{ margin: 0, fontSize: "0.75rem", color: "#718096" }}>
                                        priority <strong>{pct(it.priority)}</strong>
                                        {" · "}doubt {pct(it.uncertainty)} · rarity {pct(it.rarity)}
                                    </p>
                                </div>
                                <p style={{ margin: "0.25rem 0 0.5rem", fontSize: "0.78rem", color: "#718096" }}>
                                    {it.address || it.title || "no location"} · uploaded {it.created_at ? new Date(it.created_at).toLocaleString() : "unknown"}
                                </p>

                                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginBottom: "0.6rem" }}>
                                    {CLASSES.map(([cls, label]) => (
                                        <button key={cls} className="btn" disabled={busy}
                                            onClick={() => decide(it.issue_id, { action: "relabel", label: cls, keep_box: false })}
                                            title={`Label this photo as ${cls}`}
                                            style={{ background: it.issue_type === cls ? "#DD6B20" : "rgba(66,153,225,0.12)",
                                                color: it.issue_type === cls ? "white" : "#2C5282", border: "1px solid rgba(66,153,225,0.3)",
                                                borderRadius: "999px", padding: "0.25rem 0.7rem", fontSize: "0.75rem",
                                                fontWeight: "600", cursor: busy ? "not-allowed" : "pointer" }}>
                                            {label}
                                        </button>
                                    ))}
                                </div>

                                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", alignItems: "center" }}>
                                    {it.issue_type !== "unknown" && (
                                        <button className="btn" disabled={busy}
                                            onClick={() => decide(it.issue_id, { action: "confirm" })}
                                            style={{ background: "#2F855A", color: "white", border: "none", borderRadius: "6px", padding: "0.35rem 0.7rem", fontSize: "0.78rem", fontWeight: "600", cursor: "pointer" }}>
                                            ✓ Keep “{it.issue_type}”
                                        </button>
                                    )}
                                    {it.detections.length > 0 && (
                                        <button className="btn" disabled={busy}
                                            onClick={() => decide(it.issue_id, { action: "confirm", keep_box: true })}
                                            title="Also export the detector's bounding box as YOLO ground truth"
                                            style={{ background: "#805AD5", color: "white", border: "none", borderRadius: "6px", padding: "0.35rem 0.7rem", fontSize: "0.78rem", fontWeight: "600", cursor: "pointer" }}>
                                            ⬚ Keep box too
                                        </button>
                                    )}
                                    <button className="btn" disabled={busy}
                                        onClick={() => decide(it.issue_id, { action: "reject" })}
                                        style={{ background: "transparent", color: "#C53030", border: "1px solid #FC8181", borderRadius: "6px", padding: "0.35rem 0.7rem", fontSize: "0.78rem", fontWeight: "600", cursor: "pointer" }}>
                                        ✕ Not usable
                                    </button>
                                    {it.detections.length > 0 && (
                                        <span style={{ fontSize: "0.72rem", color: "#A0AEC0" }}>
                                            boxes drawn: {it.detections.map((d) => `${d.issue_type} ${pct(d.confidence)}`).join(", ")}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ReviewQueue;
