import { useEffect, useState } from "react";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";

const PALETTE = [
  "#E53E3E", "#DD6B20", "#3182CE", "#805AD5",
  "#D69E2E", "#38A169", "#718096", "#E53E8C",
];

const TrendCharts = () => {
  const [days, setDays] = useState(30);
  const [granularity, setGranularity] = useState("daily");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    axios
      .get(`${API_URL}/analytics/trends?days=${days}&granularity=${granularity}`)
      .then((res) => { if (alive) { setData(res.data); setLoading(false); } })
      .catch(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [days, granularity]);

  const toggle = (group, value) => {
    if (group === "days") setDays(value);
    else setGranularity(value);
  };

  const noData = !data || data.status !== "ok" || !data.labels || data.labels.length === 0;

  const datasets = data && data.by_type
    ? Object.entries(data.by_type).map(([type, values], i) => ({
        label: type.replace(/_/g, " "),
        data: values,
        borderColor: PALETTE[i % PALETTE.length],
        backgroundColor: PALETTE[i % PALETTE.length] + "22",
        borderWidth: 2,
        pointRadius: granularity === "hourly" ? 0 : 2,
        tension: 0.3,
        fill: false,
      }))
    : [];

  const chartData = {
    labels: data ? data.labels : [],
    datasets,
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    scales: {
      y: { beginAtZero: true, grid: { borderDash: [2, 4], color: "rgba(255,255,255,0.08)" }, ticks: { color: "rgba(255,255,255,0.55)" } },
      x: { grid: { display: false }, ticks: { maxTicksLimit: 12, maxRotation: 0, color: "rgba(255,255,255,0.55)" } },
    },
    plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 }, color: "rgba(255,255,255,0.7)" } } },
  };

  const hint = data
    ? `${data.total_reported} reports in window · busiest ${data.busiest || "—"}` +
      (data.peak_type ? ` · top type: ${data.peak_type.replace(/_/g, " ")}` : "")
    : "";

  const btnStyle = (active) => ({
    padding: "5px 14px", borderRadius: "8px", border: "none", cursor: "pointer",
    fontSize: "0.8rem", fontWeight: 700,
    background: active ? "#6366F1" : "rgba(255,255,255,0.08)",
    color: active ? "#fff" : "#cbd5e1",
    transition: "all 0.2s",
  });

  return (
    <div className="card" style={{
      background: "rgba(255,255,255,0.06)", borderRadius: "16px", padding: "1.5rem",
      boxShadow: "0 8px 32px rgba(0,0,0,0.18)", gridColumn: "1 / -1",
      border: "1px solid rgba(255,255,255,0.1)"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "#f1f5f9" }}>
            📈 Real-Time Reporting Trends
          </h3>
          <p style={{ margin: "3px 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
            {loading ? "Computing series…" : hint}
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <div style={{ display: "flex", gap: "6px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "10px", padding: "3px" }}>
            {[7, 30, 90].map((d) => (
              <button key={d} onClick={() => toggle("days", d)} style={btnStyle(days === d)}>{d}d</button>
            ))}
          </div>
          <div style={{ display: "flex", gap: "6px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "10px", padding: "3px" }}>
            <button onClick={() => toggle("granularity", "daily")} style={btnStyle(granularity === "daily")}>Daily</button>
            <button onClick={() => toggle("granularity", "hourly")} style={btnStyle(granularity === "hourly")}>Hourly</button>
          </div>
        </div>
      </div>

      <div style={{ marginTop: "1rem", height: "260px", position: "relative" }}>
        {loading ? (
          <div style={{ textAlign: "center", color: "#94a3b8", paddingTop: "5rem" }}>Aggregating time series…</div>
        ) : noData ? (
          <div style={{ textAlign: "center", color: "#94a3b8", paddingTop: "5rem" }}>
            Not enough dated reports to draw a trend line yet.
          </div>
        ) : (
          <Line data={chartData} options={options} />
        )}
      </div>
    </div>
  );
};

export default TrendCharts;