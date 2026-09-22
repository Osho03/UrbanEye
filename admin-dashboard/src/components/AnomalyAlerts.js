import { useEffect, useState } from "react";
import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";

const SEVERITY_STYLE = {
  Critical: { color: "#fff", bg: "#C53030", border: "#C53030" },
  High: { color: "#fff", bg: "#E53E3E", border: "#E53E3E" },
  Medium: { color: "#7B341E", bg: "#FEFCBF", border: "#D69E2E" },
};

const AnomalyAlerts = () => {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchAnomalies = () => {
      axios
        .get(`${API_URL}/analytics/anomalies`)
        .then((res) => { setResult(res.data); setError(false); })
        .catch(() => setError(true));
    };
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 45000);
    return () => clearInterval(interval);
  }, []);

  if (error) return null;
  if (!result || result.status !== "ok") return null;

  const anomalies = result.anomalies || [];

  return (
    <div style={{ marginBottom: "2rem" }}>
      {anomalies.length === 0 ? (
        <div style={{
          display: "flex", alignItems: "center", gap: "10px",
          background: "rgba(34,197,94,0.12)", border: "1px solid rgba(74,222,128,0.3)",
          borderRadius: "12px", padding: "0.7rem 1.2rem",
          color: "#4ADE80", fontSize: "0.88rem"
        }}>
          <span style={{
            width: "9px", height: "9px", borderRadius: "50%", background: "#4ADE80",
            boxShadow: "0 0 0 4px rgba(74,222,128,0.18)"
          }} />
          <strong>Anomaly Watch:</strong> no abnormal activity detected in the last {result.window_hours}h
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#FDA4AF", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{
              width: "10px", height: "10px", borderRadius: "50%", background: "#F43F5E",
              boxShadow: "0 0 0 4px rgba(244,63,94,0.2)", animation: "ane-heartbeat 1.4s infinite"
            }} />
            {result.summary}
          </div>
          {anomalies.map((a) => {
            const style = SEVERITY_STYLE[a.severity] || SEVERITY_STYLE.Medium;
            return (
              <div key={a.issue_type} style={{
                display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap",
                background: "rgba(255,255,255,0.05)",
                border: `1px solid ${style.border}`,
                borderRadius: "12px", padding: "0.7rem 1.2rem"
              }}>
                <span style={{
                  background: style.bg, color: style.color,
                  fontSize: "0.78rem", fontWeight: 800,
                  padding: "3px 12px", borderRadius: "14px"
                }}>
                  {a.severity.toUpperCase()}
                </span>
                <span style={{ flex: 1, fontSize: "0.88rem", color: "#f8fafc", minWidth: "200px" }}>
                  {a.message}
                </span>
                <span style={{
                  background: "rgba(255,255,255,0.1)", color: "#e2e8f0",
                  fontSize: "0.78rem", fontWeight: 600,
                  padding: "3px 10px", borderRadius: "10px"
                }}>
                  z-score {a.z_score.toFixed(1)}· expected {a.expected}
                </span>
              </div>
            );
          })}
        </div>
      )}

      <style>{`@keyframes ane-heartbeat { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }`}</style>
    </div>
  );
};

export default AnomalyAlerts;