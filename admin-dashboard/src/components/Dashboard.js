import { useState, useEffect } from "react";
import axios from "axios";
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title
} from "chart.js";
import { Doughnut, Bar } from "react-chartjs-2";
import PredictiveMaintenance from "./PredictiveMaintenance";
import AutonomousAgentStatus from "./AutonomousAgentStatus";

// Register ChartJS components
ChartJS.register(
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title
);

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
        // Auto-refresh stats every 10 seconds
        const interval = setInterval(fetchStats, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchStats = async () => {
        try {
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            const res = await axios.get(`${API_URL}/analytics/stats`);
            setStats(res.data);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching stats:", err);
            setLoading(false);
        }
    };

    if (loading) return <div style={{ padding: "2rem" }}>Loading dashboard...</div>;
    if (!stats) return <div style={{ padding: "2rem" }}>Error loading stats. Check backend connection.</div>;

    // --- Chart Data Config ---

    // 1. Resolution Rate (Doughnut)
    const resolutionRate = stats.total > 0 ? ((stats.resolved / stats.total) * 100).toFixed(1) : 0;
    const resolutionData = {
        labels: ["Resolved", "Unresolved"],
        datasets: [{
            data: [stats.resolved, stats.total - stats.resolved],
            backgroundColor: ["#48BB78", "#E2E8F0"],
            borderWidth: 0,
            cutout: "75%"
        }]
    };

    // 2. Department Workload (Bar)
    const deptLabels = Object.keys(stats.by_dept || {});
    const deptValues = Object.values(stats.by_dept || {});
    const deptData = {
        labels: deptLabels,
        datasets: [{
            label: "Active Tickets",
            data: deptValues,
            backgroundColor: "#4299E1",
            borderRadius: 4
        }]
    };

    // 3. Severity Distribution (Multi-color Bar)
    const sevLabels = Object.keys(stats.by_severity || {});
    const sevValues = Object.values(stats.by_severity || {});
    const severityData = {
        labels: sevLabels,
        datasets: [{
            label: "Count",
            data: sevValues,
            backgroundColor: ["#F56565", "#ED8936", "#ECC94B", "#48BB78"],
            borderRadius: 4
        }]
    };

    return (
        <div style={{ paddingBottom: "2rem" }}>
            <div className="header" style={{ marginBottom: "2rem" }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: "1.75rem", color: "#1a202c" }}>City Manager's Dashboard</h1>
                    <p style={{ margin: "0.5rem 0 0", color: "#718096" }}>Real-time overview of city infrastructure health</p>
                </div>
                <button onClick={fetchStats} className="btn btn-primary">Refresh Data</button>
            </div>

            {/* Autonomous Action */}
            <AutonomousAgentStatus />

            {/* Smart Suggestions */}
            <div style={{ marginBottom: "2rem" }}>
                <PredictiveMaintenance />
            </div>

            {/* KPI Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>

                {/* Card 1: Total Issues */}
                <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", background: "white", borderRadius: "16px", boxShadow: "0 4px 6px rgba(0,0,0,0.05)", padding: "1.5rem" }}>
                    <h3 style={{ fontSize: "0.85rem", textTransform: "uppercase", color: "#718096", margin: 0, letterSpacing: "0.05em" }}>Total Reports</h3>
                    <div style={{ fontSize: "2.5rem", fontWeight: "700", color: "#2D3748", marginTop: "1rem" }}>
                        {stats.total.toLocaleString()}
                    </div>
                </div>

                {/* Card 2: Resolution Rate (Gauge) */}
                <div className="card" style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", background: "white", borderRadius: "16px", boxShadow: "0 4px 6px rgba(0,0,0,0.05)", padding: "1.5rem" }}>
                    <h3 style={{ width: "100%", fontSize: "0.85rem", textTransform: "uppercase", color: "#718096", margin: 0, letterSpacing: "0.05em" }}>Resolution Efficiency</h3>
                    <div style={{ width: "120px", height: "120px", marginTop: "1rem", position: "relative" }}>
                        <Doughnut
                            data={resolutionData}
                            options={{ maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } } }}
                        />
                        <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", fontSize: "1.5rem", fontWeight: "bold", color: "#2D3748" }}>
                            {resolutionRate}%
                        </div>
                    </div>
                </div>

                {/* Card 3: Pending Critical (Enhanced) */}
                <div className="card" style={{ background: "linear-gradient(135deg, #fff5f5 0%, #fff 100%)", borderRadius: "16px", boxShadow: "0 4px 6px rgba(229, 62, 62, 0.1)", padding: "1.5rem", borderLeft: "4px solid #F56565" }}>
                    <h3 style={{ fontSize: "0.85rem", textTransform: "uppercase", color: "#E53E3E", margin: 0, fontWeight: "bold" }}>Attention Required</h3>
                    <div style={{ marginTop: "1.2rem", display: "flex", alignItems: "baseline", gap: "5px" }}>
                        <span style={{ fontSize: "2.5rem", fontWeight: "700", color: "#C53030" }}>{stats.pending}</span>
                        <span style={{ color: "#E53E3E" }}>issues pending</span>
                    </div>
                    <div style={{ marginTop: "1rem", height: "6px", background: "rgba(229, 62, 62, 0.1)", borderRadius: "3px" }}>
                        <div style={{ width: `${(stats.pending / (stats.total || 1)) * 100}%`, height: "100%", background: "#F56565", borderRadius: "3px" }}></div>
                    </div>
                </div>

            </div>

            {/* Charts Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "1.5rem" }}>

                {/* Chart 1: Issues by Department */}
                <div className="card" style={{ background: "white", borderRadius: "16px", padding: "1.5rem", boxShadow: "0 4px 6px rgba(0,0,0,0.05)" }}>
                    <h3 style={{ margin: "0 0 1.5rem 0", fontSize: "1rem", fontWeight: "600", color: "#4A5568" }}>Department Workload</h3>
                    <div style={{ height: "250px" }}>
                        <Bar
                            data={deptData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: { y: { beginAtZero: true, grid: { borderDash: [2, 4], color: "#EDF2F7" } }, x: { grid: { display: false } } },
                                plugins: { legend: { display: false } }
                            }}
                        />
                    </div>
                </div>

                {/* Chart 2: Severity Breakdown */}
                <div className="card" style={{ background: "white", borderRadius: "16px", padding: "1.5rem", boxShadow: "0 4px 6px rgba(0,0,0,0.05)" }}>
                    <h3 style={{ margin: "0 0 1.5rem 0", fontSize: "1rem", fontWeight: "600", color: "#4A5568" }}>Issues by Severity</h3>
                    <div style={{ height: "250px" }}>
                        <Bar
                            data={severityData}
                            options={{
                                indexAxis: 'y',
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: { x: { beginAtZero: true, grid: { borderDash: [2, 4], color: "#EDF2F7" } }, y: { grid: { display: false } } },
                                plugins: { legend: { display: false } }
                            }}
                        />
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Dashboard;
