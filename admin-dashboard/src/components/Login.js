import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const Login = ({ onLogin }) => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");

        try {
            // Use environment variable for API URL or default
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";

            const res = await axios.post(`${API_URL}/admin/login`, {
                username,
                password
            });

            if (res.data.success) {
                onLogin(res.data.token);
                navigate("/dashboard");
            }
        } catch (err) {
            setError(err.response?.data?.message || "Login failed. Check credentials.");
        }
    };

    return (
        <div className="login-container">
            <div className="login-box">
                <h2 style={{ textAlign: "center", marginBottom: "2rem" }}>🛡️ UrbanEye Admin</h2>

                {error && (
                    <div style={{
                        background: "#fed7d7",
                        color: "#c53030",
                        padding: "0.75rem",
                        borderRadius: "8px",
                        marginBottom: "1rem",
                        textAlign: "center"
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Enter username"
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                        />
                    </div>

                    <button type="submit" className="login-btn">
                        Login to Dashboard
                    </button>
                </form>

                <p style={{ textAlign: "center", marginTop: "1rem", color: "#718096", fontSize: "0.9rem" }}>
                    Authorized personnel only
                </p>
            </div>
        </div>
    );
};

export default Login;
