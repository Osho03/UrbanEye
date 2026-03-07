import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AIRecommendation.css';

/**
 * AI Recommendation Component
 * Displays AI-powered decision support for administrators
 * 
 * IMPORTANT: This is ADVISORY ONLY - AI does not auto-execute actions
 */
function AIRecommendation({ issueId }) {
    const [recommendation, setRecommendation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [collapsed, setCollapsed] = useState(false);

    useEffect(() => {
        fetchRecommendation();
        // eslint-disable-next-line
    }, [issueId]);

    const fetchRecommendation = async () => {
        try {
            setLoading(true);
            setError(null);

            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            const response = await axios.get(
                `${API_URL}/admin/issues/${issueId}/ai-recommendation`
            );

            if (response.data.success) {
                setRecommendation(response.data);
            } else {
                setError(response.data.message || 'Failed to load AI recommendation');
            }
        } catch (err) {
            console.error('AI Recommendation Error:', err);
            setError('AI service temporarily unavailable');
        } finally {
            setLoading(false);
        }
    };

    const handleAccept = () => {
        // Prefill form with AI values (implementation depends on parent component)
        alert('✅ AI recommendation accepted! Form will be pre-filled.');
        // In production: call parent callback to prefill form fields
    };

    const handleModify = () => {
        alert('✏️ You can now modify AI suggestions before submitting.');
        // In production: Enable form editing with AI values pre-filled
    };

    const handleReject = () => {
        setCollapsed(true);
    };

    if (loading) {
        return (
            <div className="ai-recommendation-card loading">
                <div className="ai-header">
                    <h3>🤖 AI Virtual City Inspector</h3>
                </div>
                <p>Analyzing issue...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="ai-recommendation-card error">
                <div className="ai-header">
                    <h3>🤖 AI Virtual City Inspector</h3>
                </div>
                <p className="error-message">⚠️ {error}</p>
            </div>
        );
    }

    if (!recommendation || collapsed) {
        return null;
    }

    const { ai_analysis, contractor_recommendations, disclaimer } = recommendation;

    return (
        <div className="ai-recommendation-card">
            <div className="ai-header">
                <h3>🤖 AI Virtual City Inspector (Advisory)</h3>
                <button className="collapse-btn" onClick={() => setCollapsed(true)}>×</button>
            </div>

            <div className="disclaimer">
                ⓘ {disclaimer}
            </div>

            {/* Confidence Meter */}
            <div className="confidence-section">
                <div className="confidence-label">
                    <span>Confidence Score</span>
                    <span className="confidence-value">{ai_analysis.confidence_score}%</span>
                </div>
                <div className="confidence-bar">
                    <div
                        className={`confidence-fill ${ai_analysis.urgency_class}`}
                        style={{ width: `${ai_analysis.confidence_score}%` }}
                    />
                </div>
            </div>

            {/* AI Recommendation */}
            <div className="recommendation-section">
                <h4>📋 Suggested Action</h4>
                <div className="recommendation-box">
                    <div className="recommendation-item">
                        <strong>Priority:</strong>
                        <span className={`priority-badge ${ai_analysis.suggested_priority.toLowerCase()}`}>
                            {ai_analysis.suggested_priority}
                        </span>
                    </div>
                    <div className="recommendation-item">
                        <strong>Action:</strong> {ai_analysis.suggested_action}
                    </div>
                    <div className="recommendation-item">
                        <strong>Priority Score:</strong> {ai_analysis.priority_score}/100
                    </div>
                </div>
            </div>

            {/* Contractor Recommendations - HONEST AI */}
            {contractor_recommendations && (
                <div className="recommendations-section">
                    <h4>🔧 Contractor Recommendations</h4>

                    {/* Check status first */}
                    {contractor_recommendations.status === 'no_data' && (
                        <div className="setup-required">
                            <div className="setup-icon">⚠️</div>
                            <h5>Setup Required</h5>
                            <p>{contractor_recommendations.message}</p>
                            <p className="setup-explanation">{contractor_recommendations.explanation}</p>
                            <button className="setup-btn">
                                Add Contractors →
                            </button>
                        </div>
                    )}

                    {contractor_recommendations.status === 'demo_data_only' && (
                        <div className="setup-required demo-warning">
                            <div className="setup-icon">🚧</div>
                            <h5>Demo Data Only</h5>
                            <p>{contractor_recommendations.message}</p>
                            <p className="setup-explanation">{contractor_recommendations.explanation}</p>
                            <button className="setup-btn">
                                Add Verified Contractors →
                            </button>
                        </div>
                    )}

                    {contractor_recommendations.status === 'no_match' && (
                        <div className="setup-required no-match">
                            <div className="setup-icon">🔍</div>
                            <h5>No Match Found</h5>
                            <p>{contractor_recommendations.message}</p>
                            <p className="setup-explanation">{contractor_recommendations.explanation}</p>
                            <button className="setup-btn">
                                Add Specialist →
                            </button>
                        </div>
                    )}

                    {contractor_recommendations.status === 'success' && contractor_recommendations.contractors && contractor_recommendations.contractors.length > 0 && (
                        <>
                            <div className="data-source-badge">
                                ✓ {contractor_recommendations.total_matches} verified contractors found
                            </div>
                            <div className="contractors-grid">
                                {contractor_recommendations.contractors.map((contractor, index) => (
                                    <div key={index} className="contractor-card">
                                        <div className="contractor-header">
                                            <span className="contractor-name">{contractor.name}</span>
                                            <span className="contractor-rating">⭐ {contractor.rating}</span>
                                        </div>
                                        <p className="contractor-specialty">{contractor.specialty}</p>
                                        <div className="contractor-details">
                                            <span className="cost">₹{contractor.cost_rate}/unit</span>
                                            <span className={`availability ${contractor.available ? 'available' : 'busy'}`}>
                                                {contractor.available ? '✓ Available' : '⌛ Busy'}
                                            </span>
                                        </div>
                                        <div className="contractor-score">
                                            <span>Suitability: {contractor.suitability_score}/100</span>
                                            <div className="score-bar">
                                                <div
                                                    className="score-fill"
                                                    style={{ width: `${contractor.suitability_score}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                        <p className="contractor-reasoning">
                                            💡 {contractor.reasoning}
                                        </p>

                                        {/* Contact Information */}
                                        <div className="contractor-contact">
                                            {contractor.phone && (
                                                <a href={`tel:${contractor.phone}`} className="contact-link" title="Call contractor">
                                                    📞 Call
                                                </a>
                                            )}
                                            {contractor.email && (
                                                <a href={`mailto:${contractor.email}`} className="contact-link" title="Send email">
                                                    ✉️ Email
                                                </a>
                                            )}
                                            {contractor.website && (
                                                <a href={contractor.website} target="_blank" rel="noopener noreferrer" className="contact-link" title="Visit website">
                                                    🌐 Website
                                                </a>
                                            )}
                                            {contractor.google_maps_route && (
                                                <a href={contractor.google_maps_route} target="_blank" rel="noopener noreferrer" className="contact-link" title="Get directions" style={{ background: 'rgba(34, 197, 94, 0.1)', borderColor: 'rgba(34, 197, 94, 0.2)', color: '#22c55e' }}>
                                                    🗺️ Directions
                                                </a>
                                            )}
                                        </div>
                                        {contractor.address && (
                                            <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '8px' }}>
                                                📍 {contractor.address}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            )}
            {/* AI Reasoning */}
            <div className="reasoning-section">
                <h4>🧠 AI Reasoning</h4>
                <ul className="reasoning-list">
                    {ai_analysis.reasoning.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                    ))}
                </ul>
            </div>

            {/* Score Breakdown */}
            <details className="score-breakdown">
                <summary>📊 View Score Breakdown</summary>
                <div className="breakdown-grid">
                    <div>Severity: {ai_analysis.score_breakdown.severity_contribution.toFixed(1)}</div>
                    <div>Impact: {ai_analysis.score_breakdown.impact_contribution.toFixed(1)}</div>
                    <div>Urgency: {ai_analysis.score_breakdown.urgency_contribution.toFixed(1)}</div>
                    <div>Context: {ai_analysis.score_breakdown.context_contribution.toFixed(1)}</div>
                </div>
            </details>

            {/* Action Buttons */}
            <div className="action-buttons">
                <button className="btn-accept" onClick={handleAccept}>
                    ✓ Accept Recommendation
                </button>
                <button className="btn-modify" onClick={handleModify}>
                    ✎ Modify & Submit
                </button>
                <button className="btn-reject" onClick={handleReject}>
                    ✗ Reject
                </button>
            </div>
        </div>
    );
}

export default AIRecommendation;
