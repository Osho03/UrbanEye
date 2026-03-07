import { useState } from 'react';
import axios from 'axios';
import './VoiceSummary.css';

const VoiceSummary = ({ issueId, description }) => {
    const [summary, setSummary] = useState(null);
    const [audio, setAudio] = useState(null);
    const [loading, setLoading] = useState(false);
    const [playing, setPlaying] = useState(false);
    const [error, setError] = useState(null);

    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

    const generateSummary = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await axios.post(`${API_URL}/admin/issues/${issueId}/summary/generate`);

            if (response.data.success) {
                setSummary(response.data.summary);
            } else {
                setError(response.data.error || 'Failed to generate summary');
            }
        } catch (err) {
            console.error('Summary generation error:', err);
            setError(err.response?.data?.error || 'AI summary not available. Please configure OpenAI API key.');
        }

        setLoading(false);
    };

    const generateVoice = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await axios.post(`${API_URL}/admin/issues/${issueId}/voice/generate`, {
                voice: 'alloy' // Can be: alloy, echo, fable, onyx, nova, shimmer
            });

            if (response.data.success) {
                setAudio(response.data.audio_url);
            } else {
                setError(response.data.error || 'Failed to generate voice');
            }
        } catch (err) {
            console.error('Voice generation error:', err);
            setError(err.response?.data?.error || 'Voice synthesis not available. Check server logs.');
        }

        setLoading(false);
    };

    const playAudio = () => {
        // Feature: Browser TTS Fallback (Best Technology, No Limits)
        // If we have a valid summary but no audio (or mock audio), use the browser.
        const shouldUseBrowserTTS = !audio || audio.includes('mock_audio') || error;

        if (shouldUseBrowserTTS) {
            if (!summary) {
                generateSummary(); // Generate text first if missing
                return;
            }
            console.log("🔊 Using Browser Native TTS (Unlimited)");
            const utterance = new SpeechSynthesisUtterance(summary);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.lang = 'en-US'; // Default to US English

            utterance.onstart = () => setPlaying(true);
            utterance.onend = () => setPlaying(false);
            utterance.onerror = (e) => {
                console.error("Browser TTS Error:", e);
                setPlaying(false);
                setError("Voice playback failed");
            };

            window.speechSynthesis.cancel(); // Stop conflicting audio
            window.speechSynthesis.speak(utterance);
            return;
        }

        // Standard backend audio playback
        const audioElement = new Audio(`${API_URL}${audio}`);

        audioElement.onplay = () => setPlaying(true);
        audioElement.onended = () => setPlaying(false);
        audioElement.onerror = () => {
            console.warn("Backend audio failed. Switching to Browser TTS.");
            setPlaying(false);
            // Retry with Browser TTS
            setError(null);
            setAudio(null); // Force browser TTS next time

            // Immediate retry
            const utterance = new SpeechSynthesisUtterance(summary || "Audio unavailable");
            window.speechSynthesis.speak(utterance);
        };

        audioElement.play();
    };

    return (
        <div className="voice-summary-container">
            <h3>🤖 AI Summary & Voice</h3>

            {error && (
                <div className="error-message">
                    ⚠️ {error}
                </div>
            )}

            {/* Summary Section */}
            <div className="summary-section">
                <div className="section-header">
                    <span>📝 Auto-Generated Summary</span>
                    <button
                        onClick={generateSummary}
                        className="btn-generate"
                        disabled={loading}
                    >
                        {loading ? '⏳ Generating...' : '🔄 Generate Summary'}
                    </button>
                </div>

                {summary ? (
                    <div className="summary-box">
                        <p>{summary}</p>
                    </div>
                ) : (
                    <div className="summary-placeholder">
                        Click "Generate Summary" to create an AI-powered summary of this issue.
                    </div>
                )}
            </div>

            {/* Voice Section */}
            <div className="voice-section">
                <div className="section-header">
                    <span>🔊 Voice Assistant</span>
                    <button
                        onClick={playAudio}
                        className="btn-voice"
                        disabled={loading || playing}
                    >
                        {playing ? '▶️ Playing...' : '🔊 Listen to Summary'}
                    </button>
                </div>

                {audio && (
                    <div className="audio-info">
                        ✅ Voice generated successfully! Click "Listen" to play.
                    </div>
                )}
            </div>
        </div>
    );
};

export default VoiceSummary;
