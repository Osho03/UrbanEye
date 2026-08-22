import { useState, useEffect } from "react";
import axios from "axios";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const TYPE_COLORS = {
    pothole: "#E53E3E",
    garbage: "#DD6B20",
    water_leak: "#3182CE",
    drainage: "#805AD5",
    streetlight: "#D69E2E",
    sidewalk_damage: "#38A169",
};

const SeasonalPatterns = () => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
        axios.get(`${API_URL}/analytics/patterns`)
            .then((res) => setData(res.data))
            .catch(() => setError(true));
    }, []);

    if (error) return null;
    if (!data) return <div className="card" style={{ padding: "1.5rem" }}>Mining seasonal patterns...</div>;

    if (data.status !== "ok") {
        return (
            <div className="card" style={{ background: "white", borderRadius: "16px", padding: "1.5rem" }}>
                <h3 style={{ margin: "0 0 0.5rem", fontSize: "1rem", fontWeight: 600, color: "#4A5568" }}>
                    📊 Seasonal Intelligence
                </h3>
                <p style={{ color: "#A0AEC0", margin: 0 }}>{data.message}</p>
            </div>
        );
    }

    const maxCount = Math.max(
        1,
        ...Object.values(data.monthly_matrix).flatMap((arr) => arr)
    );

    return (
        <div className="card" style={{
            background: "white", borderRadius: "16px", padding: "1.5rem",
            boxShadow: "0 4px 6px rgba(0,0,0,0.05)", gridColumn: "1 / -1"
        }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap" }}>
                <h3 style={{ margin: "0 0 0.2rem", fontSize: "1rem", fontWeight: 600, color: "#4A5568" }}>
                    📊 Seasonal Intelligence
                </h3>
                <span style={{ fontSize: "0.75rem", color: "#A0AEC0" }}>
                    mined from {data.total_analyzed} reports (12 months)
                </span>
            </div>

            {/* Monthly heat bars per issue type */}
            <div style={{ marginTop: "1rem", overflowX: "auto" }}>
                {Object.entries(data.monthly_matrix).map(([type, counts]) => (
                    <div key={type} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                        <span style={{ width: "130px", fontSize: "0.78rem", fontWeight: 500, color: "#4A5568" }}>
                            {type.replace(/_/g, " ")}
                        </span>
                        <div style={{ display: "flex", gap: "3px", flex: 1, minWidth: "420px" }}>
                            {counts.map((c, i) => (
                                <div key={i} title={`${MONTHS[i]}: ${c}`}
                                    style={{
                                        flex: 1, height: "16px", borderRadius: "3px",
                                        backgroundColor: TYPE_COLORS[type] || "#718096",
                                        opacity: c === 0 ? 0.08 : 0.25 + (c / maxCount) * 0.75
                                    }} />
                            ))}
                        </div>
                    </div>
                ))}
                <div style={{ display: "flex", gap: "8px", marginTop: "2px" }}>
                    <span style={{ width: "130px" }}></span>
                    <div style={{ display: "flex", gap: "3px", flex: 1, minWidth: "420px" }}>
                        {MONTHS.map((m) => (
                            <span key={m} style={{ flex: 1, textAlign: "center", fontSize: "0.62rem", color: "#A0AEC0" }}>{m}</span>
                        ))}
                    </div>
                </div>
            </div>

            {/* Spikes + recommendations */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem", marginTop: "1.2rem" }}>
                <div>
                    <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#2D3748", marginBottom: "0.4rem", textTransform: "uppercase" }}>
                        🔥 Detected Spikes
                    </div>
                    {data.spikes.length === 0 && <span style={{ color: "#A0AEC0", fontSize: "0.85rem" }}>No significant spikes.</span>}
                    {data.spikes.slice(0, 4).map((s, i) => (
                        <div key={i} style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "6px", fontSize: "0.85rem" }}>
                            <span style={{
                                background: "#FFF5F5", color: "#C53030", fontWeight: 700,
                                borderRadius: "6px", padding: "2px 7px", fontSize: "0.75rem"
                            }}>+{s.uplift_pct}%</span>
                            <span style={{ color: "#4A5568" }}>{s.issue_type.replace(/_/g, " ")} in <b>{s.month}</b> ({s.count} reports)</span>
                        </div>
                    ))}
                </div>
                <div>
                    <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "#2D3748", marginBottom: "0.4rem", textTransform: "uppercase" }}>
                        💡 Recommended Actions
                    </div>
                    {data.recommendations.map((r, i) => (
                        <div key={i} style={{
                            background: "#F0FFF4", borderLeft: "3px solid #48BB78",
                            borderRadius: "6px", padding: "6px 10px", marginBottom: "6px",
                            fontSize: "0.82rem", color: "#276749"
                        }}>{r}</div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default SeasonalPatterns;
