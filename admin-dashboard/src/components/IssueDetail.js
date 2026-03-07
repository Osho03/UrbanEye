import { useState, useEffect } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";
import AIRecommendation from "./AIRecommendation";  // Phase 10
import AIVoiceAssistant from "./AIVoiceAssistant";  // Phase 11 - Voice assistant
import VoiceSummary from "./VoiceSummary";  // Phase 13 - AI Summary & Voice Synthesis

const IssueDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [issue, setIssue] = useState(null);
    const [loading, setLoading] = useState(true);

    // Action states
    const [remarks, setRemarks] = useState("");
    const [processing, setProcessing] = useState(false);

    const [aiSummary, setAiSummary] = useState(null);

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
        fetchIssue();
        fetchAiSummary();
    }, [id]);

    const fetchAiSummary = async () => {
        try {
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            // Wait a brief moment to ensure backend analysis is ready if it's a new issue
            // CORRECT ROUTE: /api/issues (from citizen API) not /api/admin
            const res = await axios.get(`${API_URL}/issues/${id}/ai-summary`);
            setAiSummary(res.data);
        } catch (err) {
            console.error("AI Agent Offline:", err);
        }
    };

    const speakSummary = () => {
        if (!aiSummary || !aiSummary.voice_script) return;
        const utterance = new SpeechSynthesisUtterance(aiSummary.voice_script);
        // utterance.lang = 'en-IN'; // Optional: Indian English accent
        window.speechSynthesis.cancel(); // Stop previous
        window.speechSynthesis.speak(utterance);
    };

    const fetchIssue = async () => {
        try {
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            const res = await axios.get(`${API_URL}/admin/issues/${id}`);
            setIssue(res.data);
            if (res.data.admin_remarks) setRemarks(res.data.admin_remarks);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching issue:", err);
            setLoading(false);
        }
    };

    const handleVerify = async (isValid) => {
        setProcessing(true);
        try {
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            await axios.post(`${API_URL}/admin/issues/${id}/verify`, {
                is_valid: isValid,
                corrected_type: getIssueTypeString(issue.issue_type) // Or allow editing
            });
            alert("Verification saved!");
            fetchIssue();
        } catch (err) {
            alert("Error saving verification");
        } finally {
            setProcessing(false);
        }
    };

    const handleStatusUpdate = async (newStatus) => {
        setProcessing(true);
        try {
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            await axios.post(`${API_URL}/admin/issues/${id}/status`, {
                status: newStatus,
                remarks: remarks
            });
            alert(`Status updated to ${newStatus}`);
            fetchIssue();
        } catch (err) {
            alert("Error updating status");
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <div>Loading details...</div>;
    if (!issue) return <div>Issue not found</div>;

    // Safe URL generation
    let imageUrl = null;
    let isVideo = false;

    if (issue.image_path) {
        const normalizedPath = issue.image_path.replace(/\\/g, "/");
        const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
        const BASE_URL = API_URL.replace("/api", "");
        imageUrl = `${BASE_URL}/${normalizedPath}`;

        // Determine type
        const lowerPath = normalizedPath.toLowerCase();
        if (issue.media_type === "video" || lowerPath.endsWith(".mp4") || lowerPath.endsWith(".mov") || lowerPath.endsWith(".avi")) {
            isVideo = true;
        }
    }

    return (
        <div>
            <div className="header">
                <button
                    onClick={() => navigate("/issues")}
                    style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1rem" }}
                >
                    ← Back to List
                </button>
                <h1 style={{ margin: 0 }}>Issue #{id.slice(-6)}</h1>
                <span className={`badge badge-${issue.status?.toLowerCase() || 'pending'}`}>
                    {issue.status || "Pending"}
                </span>
            </div>

            <div className="detail-grid">
                {/* Left Column: AI Agent & Evidence */}
                <div className="card-column">

                    {/* NEW: AI INSPECTOR AGENT PANEL */}
                    {aiSummary && (
                        <div className="card" style={{ borderLeft: "5px solid #6b46c1", background: "#faf5ff" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <h3 style={{ margin: 0, color: "#553c9a" }}>🤖 AI Inspector Agent</h3>
                                <button onClick={speakSummary} className="btn" style={{ background: "#805ad5", color: "white", padding: "5px 10px", fontSize: "0.8rem" }}>
                                    🎤 Explain This
                                </button>
                            </div>

                            <div style={{ display: "flex", alignItems: "center", gap: "20px", marginTop: "1rem" }}>
                                <div style={{ textAlign: "center" }}>
                                    <div style={{
                                        width: "60px", height: "60px", borderRadius: "50%",
                                        background: aiSummary.priority_score > 75 ? "#e53e3e" : "#38a169",
                                        color: "white", display: "flex", alignItems: "center", justifyContent: "center",
                                        fontWeight: "bold", fontSize: "1.2rem"
                                    }}>
                                        {aiSummary.priority_score}
                                    </div>
                                    <small>Priority</small>
                                </div>
                                <div style={{ flex: 1 }}>
                                    <p style={{ margin: "0", fontWeight: "bold" }}>{aiSummary.suggested_action}</p>
                                    <div style={{ marginTop: "0.5rem" }}>
                                        {aiSummary.explanations.map((exp, idx) => (
                                            <p key={idx} style={{ margin: "2px 0", fontSize: "0.85rem", color: "#4a5568" }}>
                                                {exp}
                                            </p>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="card" style={{ borderLeft: "5px solid #2b6cb0", background: "#ebf8ff" }}>
                        <h3 style={{ margin: 0, color: "#2b6cb0" }}>📊 Impact Intelligence</h3>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "1rem" }}>
                            <div style={{ padding: "10px", background: "white", borderRadius: "8px", textAlign: "center", boxShadow: "0 2px 4px rgba(0,0,0,0.05)" }}>
                                <small style={{ color: "#718096", display: "block" }}>Repair Cost</small>
                                <strong style={{ fontSize: "1.1rem", color: "#2f855a" }}>₹{issue.estimated_repair_cost || 0}</strong>
                            </div>
                            <div style={{ padding: "10px", background: "white", borderRadius: "8px", textAlign: "center", boxShadow: "0 2px 4px rgba(0,0,0,0.05)" }}>
                                <small style={{ color: "#718096", display: "block" }}>Affected Pop.</small>
                                <strong style={{ fontSize: "1.1rem", color: "#c05621" }}>{issue.affected_population || 0}</strong>
                            </div>
                            <div style={{ padding: "10px", background: "white", borderRadius: "8px", textAlign: "center", boxShadow: "0 2px 4px rgba(0,0,0,0.05)", gridColumn: "span 2" }}>
                                <small style={{ color: "#718096", display: "block" }}>Impact Radius</small>
                                <strong style={{ fontSize: "1.1rem", color: "#2b6cb0" }}>{issue.impact_radius || 0} Meters</strong>
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <h3 style={{ marginTop: 0 }}>📸 Visual Evidence</h3>

                        {imageUrl ? (
                            isVideo ? (
                                <video
                                    src={imageUrl}
                                    controls
                                    className="detail-image"
                                    style={{ width: "100%", maxHeight: "400px", objectFit: "contain", backgroundColor: "#000" }}
                                >
                                    Your browser does not support videos.
                                </video>
                            ) : (
                                <img
                                    src={imageUrl}
                                    alt={issue.issue_type}
                                    className="detail-image"
                                    onError={(e) => { e.target.src = "https://via.placeholder.com/400?text=Image+Load+Error"; }}
                                />
                            )
                        ) : (
                            <div style={{
                                padding: "3rem",
                                textAlign: "center",
                                backgroundColor: "#f7fafc",
                                borderRadius: "8px",
                                border: "2px dashed #cbd5e0"
                            }}>
                                <p style={{ margin: 0, color: "#718096" }}>No visual evidence uploaded.</p>
                            </div>
                        )}

                        <div style={{ marginTop: "1.5rem" }}>
                            <h4>AI Analysis</h4>
                            <table className="data-table" style={{ marginTop: "0.5rem" }}>
                                <tbody>
                                    <tr>
                                        <td><strong>Detected Type</strong></td>
                                        <td style={{ textTransform: "capitalize" }}>{getIssueTypeString(issue.issue_type)}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Confidence</strong></td>
                                        <td>{((issue.confidence || 0.85) * 100).toFixed(1)}%</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Severity</strong></td>
                                        <td style={{
                                            color: issue.severity_label === "Critical" ? "red" :
                                                issue.severity_label === "High" ? "orange" : "inherit",
                                            fontWeight: "bold"
                                        }}>
                                            {issue.severity_score}/10 ({issue.severity_label})
                                        </td>
                                    </tr>
                                    {issue.forensics_data && (
                                        <tr>
                                            <td><strong>Meta Forensics</strong></td>
                                            <td>
                                                {issue.forensics_data.status === "Fresh" ? (
                                                    <span style={{ color: "green", fontWeight: "bold" }}>
                                                        ✅ Verified Fresh
                                                    </span>
                                                ) : issue.forensics_data.status === "Stale" ? (
                                                    <span style={{ color: "red", fontWeight: "bold" }}>
                                                        ⚠️ {issue.forensics_data.details}
                                                    </span>
                                                ) : issue.forensics_data.status === "Suspicious" ? (
                                                    <span style={{ color: "red", fontWeight: "bold" }}>
                                                        ⛔ {issue.forensics_data.details}
                                                    </span>
                                                ) : (
                                                    <span style={{ color: "gray" }}>
                                                        ⚪ {issue.forensics_data.details}
                                                    </span>
                                                )}
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div> {/* Close card-column */}

                {/* Right Column: Details & Actions */}
                <div className="card">
                    <h3 style={{ marginTop: 0 }}>📋 Issue Details</h3>

                    <div style={{ marginBottom: "2rem" }}>
                        <p><strong>Department:</strong> {issue.assigned_department}</p>
                        <p><strong>Location:</strong> {issue.latitude}, {issue.longitude}</p>
                        <p><strong>Description:</strong> {issue.description || "No description provided"}</p>

                        {/* Voice Note Section */}
                        {issue.voice_transcript && (
                            <div style={{
                                marginTop: "1rem",
                                padding: "1rem",
                                backgroundColor: "#f0fff4",
                                border: "1px solid #48bb78",
                                borderRadius: "8px"
                            }}>
                                <strong style={{ color: "#2f855a", display: "flex", alignItems: "center", gap: "5px" }}>
                                    🎤 Voice Note (Valid Evidence)
                                </strong>
                                <p style={{ margin: "0.5rem 0 0", fontStyle: "italic" }}>"{issue.voice_transcript}"</p>
                            </div>
                        )}

                        <p style={{ marginTop: "1rem" }}><strong>Reported:</strong> {new Date(issue.created_at).toLocaleString()}</p>
                    </div>

                    <h3>🛡️ Admin Actions</h3>

                    <div style={{ marginBottom: "1.5rem" }}>
                        <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>Admin Verification</label>
                        <div style={{ display: "flex", gap: "1rem" }}>
                            <button
                                onClick={() => handleVerify(true)}
                                disabled={processing || issue.verified}
                                className="btn btn-success"
                                style={{ flex: 1, opacity: issue.verified ? 0.5 : 1 }}
                            >
                                {issue.verified ? "Verified ✅" : "Verify as Correct"}
                            </button>
                            <button
                                onClick={() => handleVerify(false)}
                                disabled={processing}
                                className="btn btn-danger"
                                style={{ flex: 1 }}
                            >
                                Mark Incorrect
                            </button>
                        </div>
                    </div>

                    <div style={{ marginBottom: "1.5rem" }}>
                        <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>Update Status</label>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                            <button
                                onClick={() => handleStatusUpdate("Assigned")}
                                disabled={processing || issue.status === "Assigned"}
                                className="btn"
                                style={{ background: "#4299e1", color: "white" }}
                            >
                                Assign
                            </button>
                            <button
                                onClick={() => handleStatusUpdate("In Progress")}
                                disabled={processing || issue.status === "In Progress"}
                                className="btn"
                                style={{ background: "#ecc94b", color: "black" }}
                            >
                                In Progress
                            </button>
                            <button
                                onClick={() => handleStatusUpdate("Resolved")}
                                disabled={processing || issue.status === "Resolved"}
                                className="btn"
                                style={{ background: "#48bb78", color: "white" }}
                            >
                                Resolve
                            </button>
                            <button
                                onClick={() => handleStatusUpdate("Reopened")}
                                disabled={processing}
                                className="btn"
                                style={{ background: "#e53e3e", color: "white" }}
                            >
                                Reopen
                            </button>
                        </div>
                    </div>

                    <div>
                        <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "600" }}>Internal Remarks</label>
                        <textarea
                            value={remarks}
                            onChange={(e) => setRemarks(e.target.value)}
                            placeholder="Add notes for other admins..."
                            style={{ width: "100%", padding: "0.75rem", borderRadius: "8px", border: "1px solid #e2e8f0", minHeight: "80px" }}
                        />
                    </div>

                </div>
            </div>

            {/* NEW: 3D VOLUMETRIC DATA (Phase 8) */}
            {issue.volumetric_data && (
                <div className="card" style={{ marginTop: "1rem" }}>
                    <h3 style={{ marginTop: 0 }}>🏗️ Engineering & Repair Estimates</h3>
                    <div style={{ display: "flex", gap: "20px" }}>
                        {/* Depth Map */}
                        <div style={{ flex: 1 }}>
                            <p style={{ fontSize: "0.9rem", color: "#718096" }}>AI Depth Map & Topology</p>
                            {(() => {
                                const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
                                const BASE_URL = API_URL.replace("/api", "");
                                return (
                                    <img
                                        src={`${BASE_URL}/uploads/${issue.volumetric_data.depth_map_filename}`}
                                        alt="Depth Map"
                                        style={{ width: "100%", borderRadius: "8px", border: "1px solid #cbd5e0" }}
                                    />
                                );
                            })()}
                        </div>

                        {/* Metrics */}
                        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center" }}>
                            <div className="metric-box" style={{ marginBottom: "10px", padding: "10px", background: "#ebf8ff", borderRadius: "5px" }}>
                                <strong style={{ color: "#2b6cb0" }}>Est. Volume:</strong>
                                <div style={{ fontSize: "1.2rem", fontWeight: "bold" }}>{issue.volumetric_data.volume_liters} Liters</div>
                            </div>
                            <div className="metric-box" style={{ marginBottom: "10px", padding: "10px", background: "#f0fff4", borderRadius: "5px" }}>
                                <strong style={{ color: "#2f855a" }}>Material Needed (Asphalt):</strong>
                                <div style={{ fontSize: "1.2rem", fontWeight: "bold" }}>{issue.volumetric_data.material_kg} Kg</div>
                            </div>
                            <div className="metric-box" style={{ padding: "10px", background: "#fffaf0", borderRadius: "5px" }}>
                                <strong style={{ color: "#c05621" }}>Est. Repair Cost:</strong>
                                <div style={{ fontSize: "1.2rem", fontWeight: "bold" }}>₹{issue.volumetric_data.repair_cost}</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Phase 13: AI Summary & Voice Synthesis */}
            <VoiceSummary issueId={id} description={issue.description} />

            {/* Phase 10: AI-Powered Department Recommendation */}
            <AIRecommendation issueId={id} />

            {/* Phase 11: Multilingual Voice Assistant */}
            {aiSummary && aiSummary.ai_analysis && (
                <AIVoiceAssistant
                    issueId={id}
                    aiAnalysis={aiSummary.ai_analysis}
                    issueType={issue?.issue_type}
                />
            )}

        </div>
    );
};

export default IssueDetail;
