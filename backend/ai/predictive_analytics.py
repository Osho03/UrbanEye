import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formula to calculate distance (in meters) between two points.
    """
    R = 6371000 # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def detect_hotspots(issues, radius=50, min_count=3):
    """
    Identify clusters of issues to suggest predictive maintenance.
    
    Args:
        issues (list): List of issue dicts with 'latitude', 'longitude', 'issue_type'.
        radius (int): Distance in meters to consider "same location".
        min_count (int): Minimum issues to form a cluster.
        
    Returns:
        list: List of Hotspot dicts.
    """
    clusters = []
    visited = set()
    
    for i, issue1 in enumerate(issues):
        if i in visited:
            continue
            
        current_cluster = [issue1]
        visited.add(i)
        
        lat1 = float(issue1['latitude'])
        lon1 = float(issue1['longitude'])
        
        for j, issue2 in enumerate(issues):
            if j in visited:
                continue
                
            lat2 = float(issue2['latitude'])
            lon2 = float(issue2['longitude'])
            
            dist = calculate_distance(lat1, lon1, lat2, lon2)
            
            if dist <= radius:
                current_cluster.append(issue2)
                visited.add(j)
        
        if len(current_cluster) >= min_count:
            # Analyze cluster
            types = {}
            for c in current_cluster:
                itype = c.get('issue_type', 'unknown')
                # Fix: Ensure itype is a string, not a dictionary
                if isinstance(itype, dict):
                     itype = itype.get('type', 'Unknown')
                types[itype] = types.get(itype, 0) + 1
            
            # Find dominant type
            dominant_type = max(types, key=types.get)
            
            # Recommendation Logic
            recommendation = "Inspect Area"
            if dominant_type == "pothole" and len(current_cluster) >= 5:
                recommendation = "Critical: Road Resurfacing Recommended"
            elif dominant_type == "pothole":
                recommendation = "Patchwork Required"
            elif dominant_type == "garbage":
                recommendation = "Increase Sanitation Schedule"
            elif dominant_type == "streetlight":
                 recommendation = "Grid Failure Check"
            
            # Calculate Center
            avg_lat = sum(float(c['latitude']) for c in current_cluster) / len(current_cluster)
            avg_lon = sum(float(c['longitude']) for c in current_cluster) / len(current_cluster)
            
            clusters.append({
                "center": {"lat": avg_lat, "lon": avg_lon},
                "count": len(current_cluster),
                "types": types,
                "recommendation": recommendation,
                "radius": radius
            })
            
    return clusters
