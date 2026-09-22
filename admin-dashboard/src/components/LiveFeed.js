import { useEffect, useRef, useState } from "react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
const BASE_URL = API_URL.replace(/\/api$/, "");
const STREAM_URL = `${API_URL}/analytics/stream`;

const TYPE_COLORS = {
  pothole: "#E53E3E",
  garbage: "#DD6B20",
  water_leak: "#3182CE",
  drainage: "#805AD5",
  streetlight: "#D69E2E",
  sidewalk_damage: "#38A169",
  unknown: "#718096",
};

const SEVERITY_COLORS = {
  Critical: "#C53030",
  High: "#E53E3E",
  Medium: "#DD6B20",
  Low: "#38A169",
};

const typeLabel = (raw) => {
  if (!raw) return "unknown";
  if (typeof raw === "string") return raw;
  return raw.detected_type || raw.primary_guess || "unknown";
};

const timeAgo = (iso) => {
  if (!iso) return "—";
  const t = new Date(iso).getTime();
  if (Number.isNaN(t) || t <= 0) return "—";
  const s = Math.max(0, Math.floor((Date.now() - t) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
};

const LiveFeed = () => {
  const [items, setItems] = useState([]);
  const [connected, setConnected] = useState(false);
  const [arrivals, setArrivals] = useState(0);
  const seen = useRef(new Set());

  useEffect(() => {
    let es;
    try {
      es = new EventSource(STREAM_URL);
    } catch (e) {
      console.error("EventSource not supported:", e);
      return;
    }

    es.onopen = () => setConnected(true);

    const applySnapshot = (ev) => {
      try { setItems(JSON.parse(ev.data)); } catch (e) { /* ignore */ }
    };

    const applyLive = (ev) => {
      let data;
      try { data = JSON.parse(ev.data); } catch (e) { return; }
      const id = data.issue_id;
      if (!id || seen.current.has(id)) return;   // de-dupe across reconnect
      seen.current.add(id);
      setArrivals((n) => n + 1);
      setItems((prev) => [data, ...prev].slice(0, 20));
    };

    es.addEventListener("snapshot", applySnapshot);
    es.addEventListener("message", applyLive);
    es.addEventListener("update", applyLive);
    es.onerror = () => setConnected(false);

    return () => { es.close(); };
  }, []);

  return (
    <div className="card" style={{
      background: "rgba(255,255,255,0.06)",
      borderRadius: "16px",
      padding: "1.5rem",
      boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
      marginBottom: "2rem",
      borderLeft: connected ? "4px solid #4ADE80" : "4px solid #FB923C"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "#f1f5f9", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{
              width: "10px", height: "10px", borderRadius: "50%",
              background: connected ? "#4ADE80" : "#FB923C",
              boxShadow: connected ? "0 0 0 4px rgba(74,222,128,0.2)" : "0 0 0 4px rgba(251,146,60,0.2)",
              animation: connected ? "pulse 1.6s infinite" : "none"
            }} />
            Live Citizen Feed
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "#94a3b8" }}>
            {connected ? "Real-time streaming from MongoDB · new reports appear instantly" : "Reconnecting to live stream…"}
          </p>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <span style={{
            background: "rgba(34,197,94,0.15)", color: "#4ADE80", border: "1px solid rgba(74,222,128,0.35)",
            padding: "5px 14px", borderRadius: "20px", fontSize: "0.8rem", fontWeight: "bold"
          }}>
            {connected ? "🟢 LIVE" : "🔄 RECONNECTING"}
          </span>
          <span style={{ background: "rgba(56,189,248,0.15)", color: "#7DD3FC", border: "1px solid rgba(56,189,248,0.35)",
            padding: "5px 14px", borderRadius: "20px", fontSize: "0.85rem", fontWeight: "bold" }}>
            +{arrivals} this session
          </span>
        </div>
      </div>

      <div style={{
        marginTop: "1rem",
        maxHeight: "340px", overflowY: "auto",
        display: "flex", flexDirection: "column", gap: "0.5rem"
      }}>
        {items.length === 0 && (
          <div style={{ textAlign: "center", padding: "2.5rem", color: "#94a3b8", background: "rgba(255,255,255,0.04)", borderRadius: "10px", border: "1px dashed rgba(255,255,255,0.15)" }}>
            Waiting for the first report to stream in…
          </div>
        )}

        {items.map((issue) => {
          const type = typeLabel(issue.issue_type);
          const photo = issue.photo;
          const sev = issue.severity_label || "Low";
          const status = issue.status || "Pending";
          return (
            <div key={issue.issue_id || `${type}-${issue.created_at}`} style={{
              display: "flex", alignItems: "center", gap: "12px",
              background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px",
              padding: "8px 12px"
            }}>
              <img
                src={photo ? `${BASE_URL}/${photo}` : `${BASE_URL}/uploads/__missing__`}
                alt={type}
                onError={(e) => { e.target.onerror = null; e.target.src = `${BASE_URL}/uploads/__missing__`; }}
                style={{
                  width: "44px", height: "44px", objectFit: "cover",
                  borderRadius: "8px", background: "rgba(255,255,255,0.05)"
                }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                  <span style={{ fontWeight: 700, color: TYPE_COLORS[type] || "#f1f5f9", textTransform: "capitalize" }}>
                    {type.replace(/_/g, " ")}
                  </span>
                  <span style={{
                    background: SEVERITY_COLORS[sev] || "#A0AEC0", color: "#fff",
                    fontSize: "0.68rem", padding: "1px 8px", borderRadius: "10px", fontWeight: 600
                  }}>
                    {sev}
                  </span>
                  <span style={{
                    background: "rgba(255,255,255,0.08)", color: "#cbd5e1",
                    fontSize: "0.68rem", padding: "1px 8px", borderRadius: "10px", fontWeight: 600
                  }}>
                    {status}
                  </span>
                </div>
                <div style={{ fontSize: "0.78rem", color: "#94a3b8", marginTop: "2px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
                  {issue.estimated_repair_cost > 0 && <span>₹{issue.estimated_repair_cost}</span>}
                  {issue.affected_population > 0 && <span>👥 {issue.affected_population}</span>}
                  {issue.address && <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "180px" }}>📍 {issue.address}</span>}
                </div>
              </div>
              <div style={{ textAlign: "right", fontSize: "0.75rem", color: "#94a3b8", whiteSpace: "nowrap" }}>
                {timeAgo(issue.created_at)}
              </div>
            </div>
          );
        })}
      </div>

      <style>{`@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
};

export default LiveFeed;