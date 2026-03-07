import React, { useState, useEffect } from 'react';
import './AIVoiceAssistant.css';

/**
 * AI Voice Assistant Component
 * Reads AI analysis results aloud to admin using text-to-speech
 * Shows detailed breakdown of AI detection
 */

function AIVoiceAssistant({ aiAnalysis, issueType }) {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [voiceEnabled, setVoiceEnabled] = useState(true);

    // Auto-speak when AI analysis loads (optional - can be disabled)
    useEffect(() => {
        if (aiAnalysis && voiceEnabled) {
            // Auto-speak after 1 second delay
            const timer = setTimeout(() => {
                speakAIResults();
            }, 1000);

            return () => clearTimeout(timer);
        }
        // eslint-disable-next-line
    }, [aiAnalysis, voiceEnabled]);

    const speakAIResults = () => {
        if (!aiAnalysis || !('speechSynthesis' in window)) {
            console.warn('Speech synthesis not supported');
            return;
        }

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        // Build speech text
        const detectedType = aiAnalysis.detected_type || issueType || 'Unknown';
        const confidence = Math.round(aiAnalysis.confidence || 0);
        const severity = aiAnalysis.severity || 'Unknown';

        let speechText = `AI Analysis Report. `;
        speechText += `Issue detected: ${detectedType.replace(/_/g, ' ')}. `;
        speechText += `Confidence level: ${confidence} percent. `;
        speechText += `Severity: ${severity} out of 10. `;

        // Add recommendation if available
        if (aiAnalysis.suggested_action) {
            speechText += `Recommended action: ${aiAnalysis.suggested_action}. `;
        }

        // Add reasoning if available
        if (aiAnalysis.reasoning && aiAnalysis.reasoning.length > 0) {
            speechText += `Key factors: `;
            aiAnalysis.reasoning.slice(0, 3).forEach((reason) => {
                // Remove emojis for speech
                const cleanReason = reason.replace(/[^\w\s,.-]/g, '');
                speechText += `${cleanReason}. `;
            });
        }

        // Create speech utterance
        const utterance = new SpeechSynthesisUtterance(speechText);
        utterance.lang = 'en-IN'; // Indian English
        utterance.rate = 0.9; // Slightly slower for clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Event handlers
        utterance.onstart = () => {
            setIsSpeaking(true);
        };

        utterance.onend = () => {
            setIsSpeaking(false);
        };

        utterance.onerror = (event) => {
            console.error('Speech error:', event);
            setIsSpeaking(false);
        };

        // Speak it!
        window.speechSynthesis.speak(utterance);
    };

    const stopSpeaking = () => {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
    };

    if (!aiAnalysis) {
        return null;
    }

    const detectedType = aiAnalysis.detected_type || issueType || 'Unknown';
    const confidence = Math.round(aiAnalysis.confidence || 0);
    const severity = aiAnalysis.severity || 'N/A';

    return (
        <div className="ai-voice-assistant">
            <div className="assistant-header">
                <div className="assistant-title">
                    <span className="assistant-icon">🎙️</span>
                    <h4>AI Voice Assistant</h4>
                </div>

                <div className="voice-controls">
                    <button
                        className={`voice-btn ${isSpeaking ? 'speaking' : ''}`}
                        onClick={isSpeaking ? stopSpeaking : speakAIResults}
                        title={isSpeaking ? 'Stop' : 'Play AI Report'}
                    >
                        {isSpeaking ? '⏸️ Stop' : '🔊 Play Report'}
                    </button>

                    <label className="voice-toggle">
                        <input
                            type="checkbox"
                            checked={voiceEnabled}
                            onChange={(e) => setVoiceEnabled(e.target.checked)}
                        />
                        <span>Auto-play</span>
                    </label>
                </div>
            </div>

            {isSpeaking && (
                <div className="speaking-indicator">
                    <div className="sound-wave">
                        <span></span>
                        <span></span>
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <p>Reading AI analysis...</p>
                </div>
            )}

            <div className="ai-details-panel">
                <h5>📊 Detailed AI Analysis</h5>

                <div className="detail-grid">
                    <div className="detail-item">
                        <span className="detail-label">Detected Type:</span>
                        <span className="detail-value highlight">{detectedType.replace(/_/g, ' ')}</span>
                    </div>

                    <div className="detail-item">
                        <span className="detail-label">Confidence:</span>
                        <span className="detail-value">
                            <div className="confidence-bar-mini">
                                <div
                                    className="confidence-fill-mini"
                                    style={{ width: `${confidence}%` }}
                                >
                                    {confidence}%
                                </div>
                            </div>
                        </span>
                    </div>

                    <div className="detail-item">
                        <span className="detail-label">Severity:</span>
                        <span className={`detail-value severity-${severity >= 7 ? 'high' : severity >= 4 ? 'medium' : 'low'}`}>
                            {severity}/10
                        </span>
                    </div>

                    {aiAnalysis.suggested_action && (
                        <div className="detail-item full-width">
                            <span className="detail-label">Recommended Action:</span>
                            <span className="detail-value">{aiAnalysis.suggested_action}</span>
                        </div>
                    )}

                    {aiAnalysis.priority_score && (
                        <div className="detail-item">
                            <span className="detail-label">Priority Score:</span>
                            <span className="detail-value">{aiAnalysis.priority_score}/100</span>
                        </div>
                    )}
                </div>

                {
                    aiAnalysis.reasoning && aiAnalysis.reasoning.length > 0 && (
                        <div className="reasoning-compact">
                            <p className="reasoning-title">🧠 AI Reasoning:</p>
                            <ul className="reasoning-list-compact">
                                {aiAnalysis.reasoning.map((reason, idx) => (
                                    <li key={idx}>{reason}</li>
                                ))}
                            </ul>
                        </div>
                    )
                }
            </div >

            {!('speechSynthesis' in window) && (
                <div className="browser-warning">
                    ⚠️ Voice assistant not supported in this browser
                </div>
            )
            }
        </div >
    );
}

export default AIVoiceAssistant;
