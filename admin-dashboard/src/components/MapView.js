import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle, LayersControl } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import axios from "axios";
import { Link } from "react-router-dom";

// Fix for default marker icon issues in React Leaflet
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

// COMPONENT: Auto-Zoom to Fit All Markers
const MapBounds = ({ issues }) => {
    const map = useMap();
    useEffect(() => {
        if (!issues || issues.length === 0) return;
        try {
            const coords = issues
                .map(i => [parseFloat(i.latitude), parseFloat(i.longitude)])
                .filter(c => !isNaN(c[0]) && !isNaN(c[1]));

            if (coords.length > 0) {
                const bounds = L.latLngBounds(coords);
                if (bounds.isValid()) {
                    map.flyToBounds(bounds, { padding: [50, 50], duration: 1.5 });
                }
            }
        } catch (e) {
            console.error("Bounds error:", e);
        }
    }, [issues, map]);
    return null;
};

// COMPONENT: AI Heatmap Layer
const HeatmapLayer = ({ issues }) => {
    const map = useMap();
    useEffect(() => {
        if (!issues || issues.length === 0 || !L.heatLayer) return;
        const points = issues.map(i => [
            parseFloat(i.latitude),
            parseFloat(i.longitude),
            i.severity_score ? i.severity_score / 10 : 0.5
        ]);
        const heat = L.heatLayer(points, {
            radius: 35,
            blur: 20,
            maxZoom: 17,
            gradient: { 0.4: 'blue', 0.65: 'lime', 1: 'red' }
        }).addTo(map);
        return () => map.removeLayer(heat);
    }, [issues, map]);
    return null;
};

// COMPONENT: Live Admin Location
const UserMarker = () => {
    const [pos, setPos] = useState(null);
    const map = useMap();
    useEffect(() => {
        map.locate().on("locationfound", (e) => {
            setPos(e.latlng);
            // Only fly to user if it's the first time
            if (!pos) map.flyTo(e.latlng, 14);
        });
    }, [map, pos]);

    return pos ? (
        <Circle
            center={pos}
            radius={100}
            pathOptions={{ color: '#3182ce', fillColor: '#3182ce', fillOpacity: 0.3, dashArray: '5, 10' }}
        >
            <Popup>🛰️ Your Current Location (Admin)</Popup>
        </Circle>
    ) : null;
};

const MapView = () => {
    const [issues, setIssues] = useState([]);
    const [loading, setLoading] = useState(true);

    const defaultCenter = [20.5937, 78.9629]; // Center of India

    useEffect(() => {
        fetchIssues();
        const interval = setInterval(fetchIssues, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchIssues = async () => {
        try {
            const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000/api";
            const res = await axios.get(`${API_URL}/admin/issues`);
            const validIssues = res.data.filter(i =>
                !isNaN(parseFloat(i.latitude)) && !isNaN(parseFloat(i.longitude))
            );
            setIssues(validIssues);
            setLoading(false);
        } catch (err) {
            console.error("Error fetching issues for map:", err);
            setLoading(false);
        }
    };

    if (loading) return <div className="loading-map">📡 Synchronizing Geospatial Intelligence...</div>;

    return (
        <div className="map-page">
            <div className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem', background: 'white', borderRadius: '12px', marginBottom: '1rem', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#1a202c' }}>🌍 Geospatial Intelligence</h1>
                    <p style={{ margin: "4px 0 0", color: "#718096", fontSize: '0.9rem' }}>
                        Live Monitoring: {issues.length} Issues | <span style={{ color: '#38a169' }}>Real-time Feed Active</span>
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <div style={{ background: '#ebf8ff', padding: '5px 15px', borderRadius: '20px', fontSize: '0.8rem', color: '#2b6cb0', fontWeight: 'bold', border: '1px solid #bee3f8' }}>
                        🛰️ Real-time Tracking
                    </div>
                </div>
            </div>

            <div className="card" style={{ padding: 0, overflow: "hidden", height: "calc(100vh - 200px)", borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}>
                <MapContainer
                    center={defaultCenter}
                    zoom={5}
                    style={{ height: "100%", width: "100%" }}
                >
                    <LayersControl position="topright">
                        <LayersControl.BaseLayer checked name="Modern Canvas">
                            <TileLayer
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />
                        </LayersControl.BaseLayer>
                        <LayersControl.BaseLayer name="High-Fidelity Satellite">
                            <TileLayer
                                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                                attribution='Tiles &copy; Esri &mdash; Source: Esri'
                            />
                        </LayersControl.BaseLayer>

                        <LayersControl.Overlay checked name="AI Problem Density (Heatmap)">
                            <HeatmapLayer issues={issues} />
                        </LayersControl.Overlay>
                    </LayersControl>

                    <MapBounds issues={issues} />
                    <UserMarker />

                    {issues.map((issue) => {
                        const lat = parseFloat(issue.latitude);
                        const lng = parseFloat(issue.longitude);
                        if (isNaN(lat) || isNaN(lng)) return null;

                        return (
                            <div key={issue.issue_id || Math.random()}>
                                <Marker position={[lat, lng]}>
                                    <Popup className="custom-popup">
                                        <div style={{ minWidth: "220px", padding: '5px' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                                <span className={`badge badge-${issue.status?.toLowerCase()}`} style={{ fontSize: '0.7rem' }}>
                                                    {issue.status}
                                                </span>
                                                <span style={{ fontSize: '0.7rem', color: '#718096' }}>#{issue.issue_id?.slice(-4)}</span>
                                            </div>
                                            <h3 style={{ margin: "0 0 5px 0", fontSize: '1.1rem', textTransform: "capitalize" }}>
                                                {issue.issue_type}
                                            </h3>
                                            <p style={{ margin: "0 0 10px 0", fontSize: "0.85rem", color: "#4a5568" }}>
                                                📍 {issue.address || "Location Detected"}
                                            </p>
                                            <div style={{ borderTop: '1px solid #edf2f7', paddingTop: '10px' }}>
                                                <Link
                                                    to={`/issues/${issue.issue_id}`}
                                                    style={{ display: "block", textAlign: 'center', background: '#2b6cb0', color: 'white', padding: '8px', borderRadius: '6px', textDecoration: "none", fontWeight: "bold", fontSize: '0.8rem' }}
                                                >
                                                    Investigate Issue →
                                                </Link>
                                            </div>
                                        </div>
                                    </Popup>
                                </Marker>
                                {issue.impact_radius > 0 && (
                                    <Circle
                                        center={[lat, lng]}
                                        radius={issue.impact_radius}
                                        pathOptions={{
                                            color: issue.severity_label === "High" ? "#e53e3e" : (issue.severity_label === "Medium" ? "#dd6b20" : "#3182ce"),
                                            fillColor: issue.severity_label === "High" ? "#e53e3e" : (issue.severity_label === "Medium" ? "#dd6b20" : "#3182ce"),
                                            fillOpacity: 0.15,
                                            weight: 1
                                        }}
                                    />
                                )}
                            </div>
                        );
                    })}
                </MapContainer>
            </div>
        </div>
    );
};

export default MapView;
