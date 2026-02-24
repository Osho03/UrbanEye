"""
UrbanEye AI - Internal Contractor Registry
Admin-controlled contractor database (Mock data for demonstration)

IMPORTANT: 
- Contractors are NOT public
- Contractors are NOT self-registered
- Admin controls this list
- AI uses this data for advisory recommendations only
"""

# Mock Contractor Database
# In production, this would be a MongoDB collection or SQL table

CONTRACTORS = [
    {
        "id": "CTR001",
        "name": "ABC Road Contractors Pvt Ltd",
        "specialty": "Roads & Infrastructure",
        "specialties": ["Pothole", "Road Damage", "Sidewalk Damage"],
        "rating": 4.5,
        "cost_rate": 500,  # ₹ per sq meter
        "available": True,
        "phone": "+91-9876543210",
        "email": "contact@abcroads.com",
        "website": "https://abcroadcontractors.com",
        "google_maps_route": "https://www.google.com/maps/dir/?api=1&destination=ABC+Road+Contractors+Mumbai",
        "address": "123 Main Road, Andheri West, Mumbai 400053",
        "completed_jobs": 245,
        "avg_completion_time": 2  # days
    },
    {
        "id": "CTR002",
        "name": "XYZ Sanitation Services",
        "specialty": "Water & Sanitation",
        "specialties": ["Water Leak", "Garbage Dump", "Drainage Issue"],
        "rating": 4.2,
        "cost_rate": 300,  # ₹ per unit
        "available": True,
        "phone": "+91-9876543211",
        "email": "info@xyzsanitation.com",
        "website": "https://xyzsanitation.in",
        "google_maps_route": "https://www.google.com/maps/dir/?api=1&destination=XYZ+Sanitation+Services+Mumbai",
        "address": "456 Service Lane, Bandra East, Mumbai 400051",
        "completed_jobs": 189,
        "avg_completion_time": 1  # days
    },
    {
        "id": "CTR003",
        "name": "City Electricals & Lighting Co.",
        "specialty": "Electrical & Lighting",
        "specialties": ["Streetlight", "Electrical Hazard"],
        "rating": 4.8,
        "cost_rate": 200,  # ₹ per unit
        "available": True,
        "phone": "+91-9876543212",
        "email": "support@cityelectricals.com",
        "website": "https://cityelectricals.co.in",
        "google_maps_route": "https://www.google.com/maps/dir/?api=1&destination=City+Electricals+Mumbai",
        "address": "789 Power House Road, Kurla West, Mumbai 400070",
        "completed_jobs": 412,
        "avg_completion_time": 1  # days
    },
    {
        "id": "CTR004",
        "name": "Metro General Contractors",
        "specialty": "General Maintenance",
        "specialties": ["General", "Sidewalk Damage", "Public Property Damage"],
        "rating": 3.9,
        "cost_rate": 400,  # ₹ per unit
        "available": False,  # Currently busy
        "phone": "+91-9876543213",
        "email": "metro@contractors.com",
        "website": "https://metrocontractors.in",
        "google_maps_route": "https://www.google.com/maps/dir/?api=1&destination=Metro+General+Contractors+Mumbai",
        "address": "321 Industrial Estate, Goregaon East, Mumbai 400063",
        "completed_jobs": 156,
        "avg_completion_time": 3  # days
    },
    {
        "id": "CTR005",
        "name": "GreenCity Waste Management",
        "specialty": "Waste & Sanitation",
        "specialties": ["Garbage Dump", "Drainage Issue"],
        "rating": 4.4,
        "cost_rate": 250,  # ₹ per unit
        "available": True,
        "phone": "+91-9876543214",
        "email": "greencity@waste.com",
        "website": "https://greencitywaste.co.in",
        "google_maps_route": "https://www.google.com/maps/dir/?api=1&destination=GreenCity+Waste+Management+Mumbai",
        "address": "567 Green Park, Powai, Mumbai 400076",
        "completed_jobs": 298,
        "avg_completion_time": 1  # days
    }
]


def get_all_contractors():
    """Returns all contractors (admin view)"""
    return CONTRACTORS


def get_contractors_by_specialty(specialties):
    """
    Get contractors matching specific specialties
    
    Args:
        specialties: List of required specialties
        
    Returns:
        List of matching contractors
    """
    matching = []
    for contractor in CONTRACTORS:
        for specialty in specialties:
            if specialty in contractor.get("specialties", []):
                matching.append(contractor)
                break
    return matching


def get_available_contractors():
    """Returns only available contractors"""
    return [c for c in CONTRACTORS if c.get("available", False)]


def get_contractor_by_id(contractor_id):
    """Get specific contractor by ID"""
    for contractor in CONTRACTORS:
        if contractor["id"] == contractor_id:
            return contractor
    return None
