import { useState, useEffect } from "react";
import axios from "axios";
import { Link } from "react-router-dom";

const IssueList = () => {
    const [issues, setIssues] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("All");
    const [search, setSearch] = useState("");

    // Helper function to safely get issue type string
    const getIssueTypeString = (issueType) => {
        if (!issueType) return 'Unknown';
        if (typeof issueType === 'string') return issueType;
        if (typeof issueType === 'object') {
            // Phase 12: AI returns object when uncertain
            return issueType.detected_type || issueType.primary_guess || 'Unknown';
        }
        return String(issueType);
    };

    useEffect(() => {
        fetchIssues();
    }, []);

    const fetchIssues = async () => {
        try {
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            // Get base URL for media (remove /api)
            const BASE_URL = API_URL.replace("/api", "");
            const res = await axios.get(`${API_URL}/admin/issues`);
            setIssues(res.data);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching issues:", err);
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case "Pending": return "badge badge-pending";
            case "Assigned": return "badge badge-assigned";
            case "Resolved": return "badge badge-resolved";
            default: return "badge";
        }
    };

    const filteredIssues = issues.filter(issue => {
        const matchesFilter = filter === "All" || issue.status === filter;

        // Safe string conversion - handle cases where values might not be strings
        const issueType = typeof issue.issue_type === 'string' ? issue.issue_type : String(issue.issue_type || '');
        const description = typeof issue.description === 'string' ? issue.description : String(issue.description || '');
        const department = typeof issue.assigned_department === 'string' ? issue.assigned_department : String(issue.assigned_department || '');

        const matchesSearch = issueType.toLowerCase().includes(search.toLowerCase()) ||
            description.toLowerCase().includes(search.toLowerCase()) ||
            department.toLowerCase().includes(search.toLowerCase());

        return matchesFilter && matchesSearch;
    });

    if (loading) return <div>Loading issues...</div>;

    return (
        <div>
            <div className="header" style={{ background: 'white', padding: '1.5rem 2rem', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#1a202c' }}>🛡️ Issue Management Intelligence</h1>
                    <p style={{ margin: "4px 0 0", color: "#718096", fontSize: '0.9rem' }}>
                        Autonomous Monitoring: {issues.length} Active Incidents
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <div style={{ background: '#f0fff4', padding: '5px 15px', borderRadius: '20px', fontSize: '0.8rem', color: '#2f855a', fontWeight: 'bold', border: '1px solid #c6f6d5', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span style={{ width: '8px', height: '8px', background: '#38a169', borderRadius: '50%', display: 'inline-block' }}></span>
                        Live Signal
                    </div>
                    <button onClick={fetchIssues} className="btn" style={{ background: '#2b6cb0', color: 'white', padding: '8px 16px', borderRadius: '8px', fontSize: '0.85rem' }}>
                        Refresh Feed
                    </button>
                </div>
            </div>

            <div className="card" style={{ padding: '1.5rem', borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}>
                <div style={{ display: "flex", gap: "1rem", marginBottom: "1.5rem" }}>
                    <div style={{ position: 'relative', flex: 1 }}>
                        <input
                            placeholder="Search Intelligent Logs..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            style={{ width: '100%', padding: "0.75rem 1rem 0.75rem 2.5rem", borderRadius: "10px", border: "1px solid #e2e8f0", background: '#f8fafc' }}
                        />
                        <span style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.4 }}>🔍</span>
                    </div>
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        style={{ padding: "0.5rem 1rem", borderRadius: "10px", border: "1px solid #e2e8f0", background: 'white', fontWeight: '600', color: '#4a5568' }}
                    >
                        <option value="All">All Intelligence Tags</option>
                        <option value="Pending">🔴 Pending Review</option>
                        <option value="Assigned">🔵 In Progress</option>
                        <option value="Resolved">🟢 Resolved</option>
                    </select>
                </div>

                <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                        <thead style={{ background: '#f8fafc' }}>
                            <tr>
                                <th style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Visual Evidence</th>
                                <th style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Description</th>
                                <th style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>AI Classification</th>
                                <th style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Response Unit</th>
                                <th style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Timestamp</th>
                                <th style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Security Status</th>
                                <th style={{ color: '#64748b', textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.05em' }}>Operations</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredIssues.map((issue) => {
                                // ... (rest of map logic remains same, just styling updates)
                                let thumbUrl = null;
                                let isVideo = false;
                                if (issue.image_path) {
                                    const normalizedPath = issue.image_path.replace(/\\/g, "/");
                                    const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
                                    const BASE_URL = API_URL.replace("/api", "");
                                    thumbUrl = `${BASE_URL}/${normalizedPath}`;
                                    const lower = normalizedPath.toLowerCase();
                                    if (issue.media_type === "video" || lower.endsWith(".mp4") || lower.endsWith(".mov")) {
                                        isVideo = true;
                                    }
                                }

                                return (
                                    <tr key={issue.issue_id || Math.random()}>
                                        <td style={{ padding: '1rem' }}>
                                            {thumbUrl ? (
                                                isVideo ? (
                                                    <div style={{ width: '60px', height: '60px', background: '#f1f5f9', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.05)' }}>
                                                        🎥
                                                    </div>
                                                ) : (
                                                    <img
                                                        src={thumbUrl}
                                                        alt="evidence"
                                                        style={{ width: "60px", height: "60px", objectFit: "cover", borderRadius: "10px", border: "2px solid white", boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}
                                                        onError={(e) => e.target.src = 'https://via.placeholder.com/60?text=Error'}
                                                    />
                                                )
                                            ) : (
                                                <div style={{ width: '60px', height: '60px', background: '#f8fafc', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed #e2e8f0' }}>
                                                    <span style={{ fontSize: '1.2rem', opacity: 0.3 }}>📷</span>
                                                </div>
                                            )}
                                        </td>
                                        <td style={{ verticalAlign: 'middle' }}>
                                            <div style={{ maxWidth: "200px", fontWeight: '500', color: '#1e293b' }}>
                                                {issue.description || <em style={{ color: "#94a3b8" }}>Encrypted or Null</em>}
                                            </div>
                                        </td>
                                        <td style={{ verticalAlign: 'middle' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                                                <span style={{ fontWeight: "700", color: '#475569', textTransform: "capitalize" }}>
                                                    {getIssueTypeString(issue.issue_type)}
                                                </span>
                                                {issue.verified && <span title="AI Verified" style={{ fontSize: '1rem' }}>🛡️</span>}
                                            </div>
                                        </td>
                                        <td style={{ verticalAlign: 'middle', color: '#64748b', fontSize: '0.9rem' }}>{issue.assigned_department || "Awaiting Dispatch"}</td>
                                        <td style={{ verticalAlign: 'middle', color: '#64748b', fontSize: '0.85rem' }}>
                                            {issue.created_at ? new Date(issue.created_at).toLocaleString() : "Syncing..."}
                                        </td>
                                        <td style={{ verticalAlign: 'middle' }}>
                                            <span className={getStatusBadge(issue.status || "Pending")} style={{ borderRadius: '6px' }}>
                                                {issue.status || "Pending"}
                                            </span>
                                        </td>
                                        <td style={{ verticalAlign: 'middle' }}>
                                            <Link
                                                to={`/issues/${issue.issue_id}`}
                                                className="btn"
                                                style={{ background: '#f1f5f9', color: '#334155', textDecoration: "none", fontSize: "0.8rem", padding: "8px 12px", borderRadius: '8px', border: '1px solid #e2e8f0', fontWeight: 'bold', transition: 'all 0.2s' }}
                                            >
                                                Inspect 🔍
                                            </Link>
                                        </td>
                                    </tr>
                                );
                            })}

                            {filteredIssues.length === 0 && (
                                <tr>
                                    <td colSpan="7" style={{ textAlign: "center", padding: "5rem 2rem" }}>
                                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📡</div>
                                        <h3 style={{ margin: 0, color: '#475569' }}>Synchronizing Real-time Feed...</h3>
                                        <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>The database is clean and waiting for the next user report.</p>
                                        <button onClick={fetchIssues} className="btn" style={{ marginTop: '1.5rem', background: '#2b6cb0', color: 'white' }}>Check for New Signals</button>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default IssueList;
