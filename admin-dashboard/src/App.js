import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import "./App.css";

// Components
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import IssueList from "./components/IssueList";
import IssueDetail from "./components/IssueDetail";
import MapView from "./components/MapView";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem("adminToken")
  );

  useEffect(() => {
    // Check auth on mount
    setIsAuthenticated(!!localStorage.getItem("adminToken"));
  }, []);

  const handleLogin = (token) => {
    localStorage.setItem("adminToken", token);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("adminToken");
    setIsAuthenticated(false);
  };

  // Protected Route Wrapper
  const ProtectedRoute = ({ children }) => {
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    return children;
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ?
              <Navigate to="/dashboard" replace /> :
              <Login onLogin={handleLogin} />
          }
        />

        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <div className="admin-container">
                <nav className="sidebar">
                  <h2>🛡️ UrbanEye Admin</h2>
                  <a href="/dashboard" className="nav-link">📊 Dashboard</a>
                  <a href="/issues" className="nav-link">📋 Issue Management</a>
                  <a href="/map" className="nav-link">🌍 Map View</a>
                  <button onClick={handleLogout} className="logout-btn">Logout</button>
                </nav>
                <div className="main-content">
                  <Routes>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/issues" element={<IssueList />} />
                    <Route path="/issues/:id" element={<IssueDetail />} />
                    <Route path="/map" element={<MapView />} />
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  </Routes>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
