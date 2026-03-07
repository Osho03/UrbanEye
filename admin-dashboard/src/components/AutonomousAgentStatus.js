import React, { useState, useEffect } from "react";
import axios from "axios";

const AutonomousAgentStatus = () => {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(false);
    const [triggering, setTriggering] = useState(false);

    const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";

    const fetchStatus = async () => {
        try {
            const res = await axios.get(`${API_URL}/admin/autonomous/status`);
            setStatus(res.data);
        } catch (err) {
            console.error("Error fetching agent status:", err);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleTrigger = async () => {
        setTriggering(true);
        try {
            const res = await axios.post(`${API_URL}/admin/autonomous/trigger`);
            alert(res.data.message);
            fetchStatus();
        } catch (err) {
            alert("Error triggering agent: " + (err.response?.data?.error || err.message));
        } finally {
            setTriggering(false);
        }
    };

    return (
        <div className="card" style={{
            background: "linear-gradient(135deg, #ebf8ff 0%, #fff 100%)",
            borderRadius: "16px",
            padding: "1.5rem",
            boxShadow: "0 4px 6px rgba(66, 153, 225, 0.1)",
            borderLeft: "4px solid #4299E1",
            marginBottom: "2rem"
        }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                    <h3 style={{ fontSize: "0.85rem", textTransform: "uppercase", color: "#2B6CB0", margin: 0, fontWeight: "bold" }}>Agentic AI: Autonomous Worker</h3>
                    <p style={{ margin: "5px 0 0", fontSize: "0.9rem", color: "#4A5568" }}>
                        Currently overseeing <strong>{status?.auto_processed_total || 0}</strong> automated resolutions.
                    </p>
                </div>
                <button
                    onClick={handleTrigger}
                    disabled={triggering}
                    className="btn"
                    style={{
                        background: triggering ? "#A0AEC0" : "#4299E1",
                        color: "white",
                        padding: "0.6rem 1.2rem",
                        borderRadius: "8px",
                        border: "none",
                        fontWeight: "600",
                        cursor: triggering ? "not-allowed" : "pointer",
                        transition: "all 0.2s"
                    }}
                >
                    {triggering ? "🤖 Working..." : "⚡ Trigger Autonomous Run"}
                </button>
            </div>

            {status?.recent_actions?.length > 0 && (
                <div style={{ marginTop: "1rem", borderTop: "1px solid rgba(66, 153, 225, 0.1)", paddingTop: "1rem" }}>
                    <p style={{ fontSize: "0.75rem", color: "#718096", marginBottom: "5px", textTransform: "uppercase" }}>Recent Autonomous Activity:</p>
                    <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                        {status.recent_actions.slice(0, 3).map((log, i) => (
                            <div key={i} style={{
                                background: "rgba(66, 153, 225, 0.05)",
                                padding: "4px 10px",
                                borderRadius: "4px",
                                fontSize: "0.8rem",
                                color: "#2C5282"
                            }}>
                                🤖 Processed {log.issues_processed} issues ({new Date(log.timestamp).toLocaleTimeString()})
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AutonomousAgentStatus;
