import math

def calculate_impact_radius(latitude, longitude, severity_score, db_context=None):
    """
    Calculate civic impact radius based on GPS data and issue severity.
    
    Args:
        latitude (float): Latitude of the reported issue
        longitude (float): Longitude of the reported issue
        severity_score (str): 'Low', 'Medium', or 'High'
        db_context (dict): Optional DB objects for nearby issue lookup (for advanced logic)
        
    Returns:
        dict: impact_radius (meters) and affected_population (estimate)
    """
    # Base radius based on severity
    severity_weights = {
        "Low": 50,      # 50 meters
        "Medium": 150,  # 150 meters
        "High": 300     # 300 meters
    }
    
    base_radius = severity_weights.get(severity_score, 100)
    
    # Simple affected population estimate (approx 0.05 persons per sqm in urban areas)
    # Area = pi * r^2
    area_sqm = math.pi * (base_radius ** 2)
    population_estimate = int(area_sqm * 0.05)
    
    return {
        "impact_radius": base_radius,
        "affected_population": population_estimate
    }
