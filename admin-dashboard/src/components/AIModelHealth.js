import React, { useState, useEffect } from "react";
import axios from "axios";

const AIModelHealth = () => {
    const [health, setHealth] = useState(null);
    const [running, setRunning] = useState(false);

    const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";

    const fetchHealth = async () => {
        try {
            const res = await axios.get(`${API_URL}/analytics/model-health`);
            setHealth(res.data);
            setRunning(res.data?.benchmark?.running === true);
        } catch (err) {
            console.error("Error fetching model health:", err);
        }
    };

    useEffect(() => {
        fetchHealth();
        const interval = setInterval(fetchHealth, 15000);
        return () => clearInterval(interval);
    }, []);

    const handleBenchmark = async () => {
        setRunning(true);
        try {
            await axios.post(`${API_URL}/analytics/benchmark`);
            // poll until the async job finishes
            const poll = setInterval(async () => {
                try {
                    const res = await axios.get(`${API_URL}/analytics/model-health`);
                    setHealth(res.data);
                    if (res.data?.benchmark?.running !== true) {
                        setRunning(false);
                        clearInterval(poll);
                    }
                } catch (e) {
                    clearInterval(poll);
                    setRunning(false);
                }
            }, 7000);
        } catch (err) {
            alert("Error starting benchmark: " + (err.response?.data?.error || err.message));
            setRunning(false);
        }
    };

    if (!health) return null;

    const evalModels = health.eval?.models || {};
    const yolo = evalModels.yolov8_onnx?.metrics;
    const mobilenet = evalModels.mobilenetv2?.metrics;
    const charts = health.charts || {};
    const decision = health.last_decision || null;

    const pct = (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "--");
    const decideText = () => {
        if (!decision) return "Collecting citizen data — first retrain comes after enough new verified photos arrive.";
        if (decision.verdict === "promoted")
            return `Last retrain (${pct(decision.candidate_acc)}) improved on the live model — weights promoted automatically.`;
        if (decision.verdict === "rejected")
            return `Last retrain was BLOCKED by the regression guard (${pct(decision.candidate_acc)} < live ${pct(decision.live_acc)}); the stronger model is still live.`;
        return "Auto-retrain loop checked; waiting for new data.";
    };

    const AccBar = ({ label, metrics, color }) => (
        <div style={{ marginTop: "0.9rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#4A5568", marginBottom: "5px" }}>
                <span style={{ fontWeight: "600" }}>{label}</span>
                <span style={{ fontWeight: "700", color }}>
                    {pct(metrics?.accuracy)} <span style={{ fontWeight: "400", color: "#A0AEC0" }}>F1 {pct(metrics?.macro_f1)}</span>
                </span>
            </div>
            <div style={{ height: "8px", background: "rgba(66,153,225,0.10)", borderRadius: "4px", overflow: "hidden" }}>
                <div style={{ width: `${(metrics?.accuracy || 0) * 100}%`, height: "100%", background: `linear-gradient(90deg, ${color}99, ${color})`, borderRadius: "4px", transition: "width 0.8s" }} />
            </div>
        </div>
    );

    const chartList = [
        ["Detector Confusion Matrix", charts["yolov8_onnx/confusion"]],
        ["Classifier Confusion Matrix", charts["mobilenetv2/confusion"]],
        ["Class Performance (Precision/Recall/F1)", charts["mobilenetv2/performance"]],
    ].filter(([, url]) => url);

    return (
        <div className="card" style={{
            background: "linear-gradient(135deg, #f0fff4 0%, #fff 100%)",
            borderRadius: "16px",
            padding: "1.5rem",
            boxShadow: "0 4px 6px rgba(72, 187, 120, 0.1)",
            borderLeft: "4px solid #48BB78",
            marginBottom: "2rem"
        }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                <div>
                    <h3 style={{ fontSize: "0.85rem", textTransform: "uppercase", color: "#2F855A", margin: 0, fontWeight: "bold" }}>
                        AI Model Health · Self-improving Pipeline
                    </h3>
                    <p style={{ margin: "5px 0 0", fontSize: "0.9rem", color: "#4A5568" }}>
                        <strong>{health.dataset_images || 0}</strong> verified citizen photos in the training set
                        {" · "}
                        {health.auto_retrain_enabled
                            ? <span style={{ color: "#2F855A", fontWeight: "600" }}>self-training ACTIVE (checks every {health.thresholds?.schedule_minutes || 30} min)</span>
                            : <span style={{ color: "#A0AEC0" }}>auto-retrain disabled on this host</span>}
                    </p>
                </div>
                <button
                    onClick={handleBenchmark}
                    disabled={running}
                    className="btn"
                    style={{
                        background: running ? "#A0AEC0" : "#48BB78",
                        color: "white",
                        padding: "0.6rem 1.2rem",
                        borderRadius: "8px",
                        border: "none",
                        fontWeight: "600",
                        cursor: running ? "not-allowed" : "pointer",
                        transition: "all 0.2s"
                    }}
                >
                    {running ? "⚙ Re-benchmarking models…" : "🔬 Run Benchmark Now"}
                </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem", marginTop: "1.25rem" }}>
                <div>
                    <AccBar label="Object Detector (YOLOv8)" metrics={yolo} color="#ED8936" />
                    <AccBar label="Image Classifier (MobileNetV2)" metrics={mobilenet} color="#4299E1" />
                    <p style={{ fontSize: "0.72rem", color: "#718096", marginTop: "0.75rem" }}>
                        Tested against <strong>{health.eval?.n_samples || 0}</strong> held-out citizen photos on {health.eval?.generated_at || "—"}.
                    </p>
                </div>

                <div style={{ display: "flex", flexDirection: "column" }}>
                    <p style={{ margin: 0, fontSize: "0.8rem", color: "#2F855A", fontWeight: "600" }}>
                        {running ? "Re-measuring every model now…" : "Forecast / Guard State"}
                    </p>
                    <p style={{ fontSize: "0.85rem", color: "#4A5568", marginTop: "0.4rem", lineHeight: 1.5 }}>
                        {decideText()}
                    </p>
                    {(decision?.verdict === "promoted" || decision?.verdict === "rejected") && (
                        <p style={{ fontSize: "0.75rem", color: "#718096", marginTop: "0.4rem" }}>
                            {health.runs || 0} training run(s) · dataset grew from {health.trained_samples || 0} → {health.dataset_images || 0} photos
                            {health.last_trained_at ? ` · last trained ${new Date(health.last_trained_at).toLocaleString()}` : ""}
                        </p>
                    )}
                </div>
            </div>

            {chartList.length > 0 && (
                <div style={{ marginTop: "1.25rem", borderTop: "1px solid rgba(72,187,120,0.15)", paddingTop: "1rem" }}>
                    <p style={{ fontSize: "0.75rem", color: "#718096", marginBottom: "0.75rem", textTransform: "uppercase" }}>Live Benchmark Charts</p>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1rem" }}>
                        {chartList.map(([label, url]) => (
                            <div key={label} style={{ background: "#fff", borderRadius: "12px", padding: "0.75rem", boxShadow: "0 2px 6px rgba(0,0,0,0.04)" }}>
                                <p style={{ fontSize: "0.75rem", fontWeight: "600", color: "#2D3748", margin: "0 0 0.5rem" }}>{label}</p>
                                <img src={url} alt={label} style={{ width: "100%", borderRadius: "8px" }} onError={(e) => (e.target.style.visibility = "hidden")} />
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AIModelHealth;