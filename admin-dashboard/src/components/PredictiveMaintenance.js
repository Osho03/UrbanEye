import { useState, useEffect } from "react";
import axios from "axios";

const PredictiveMaintenance = () => {
    const [hotspots, setHotspots] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHotspots = async () => {
            try {
                const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
                const res = await axios.get(`${API_URL}/analytics/hotspots`);
                setHotspots(res.data);
                setLoading(false);
            } catch (err) {
                console.error("Error fetching hotspots:", err);
                setLoading(false);
            }
        };

        fetchHotspots();
        // Poll every 30 seconds
        const interval = setInterval(fetchHotspots, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="card">Loading Intelligence...</div>;

    if (hotspots.length === 0) {
        return (
            <div className="card" style={{ borderLeft: "4px solid #48bb78" }}>
                <h3 style={{ marginTop: 0 }}>🧠 Predictive AI</h3>
                <p>No critical hotspots detected. City maintenance is stable.</p>
            </div>
        );
    }

    return (
        <div className="card" style={{ borderLeft: "4px solid #e53e3e", backgroundColor: "#fff5f5" }}>
            <h3 style={{ marginTop: 0, color: "#c53030", display: "flex", alignItems: "center", gap: "10px" }}>
                🧠 Predictive Maintenance Required
                <span className="badge badge-pending">{hotspots.length} Zones</span>
            </h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {hotspots.map((hotspot, index) => (
                    <div key={index} style={{
                        background: "white",
                        padding: "1rem",
                        borderRadius: "8px",
                        border: "1px solid #fc8181",
                        boxShadow: "0 2px 4px rgba(0,0,0,0.05)"
                    }}>
                        <h4 style={{ margin: "0 0 0.5rem 0", color: "#e53e3e" }}>
                            ⚠️ {hotspot.recommendation}
                        </h4>
                        <div style={{ fontSize: "0.9rem", color: "#4a5568" }}>
                            <p style={{ margin: "0.25rem 0" }}>
                                <strong>Density:</strong> {hotspot.count} issues within {hotspot.radius}m
                            </p>
                            <p style={{ margin: "0.25rem 0" }}>
                                <strong>Location:</strong> {hotspot.center.lat.toFixed(5)}, {hotspot.center.lon.toFixed(5)}
                            </p>
                            <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem" }}>
                                {Object.entries(hotspot.types).map(([type, count]) => (
                                    <span key={type} className="badge" style={{ background: "#edf2f7", color: "#2d3748" }}>
                                        {count} {type}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PredictiveMaintenance;
