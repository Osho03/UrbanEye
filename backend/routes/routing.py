# Department Routing Rules

# Maps issue types to specific government departments and priority levels
DEPARTMENT_RULES = {
    "pothole": {
        "dept": "Road Department",
        "priority": "High"
    },
    "garbage": {
        "dept": "Sanitation Department",
        "priority": "Medium"
    },
    "water_leak": {
        "dept": "Water Board",
        "priority": "High"
    },
    "streetlight": {
        "dept": "Electricity Department",
        "priority": "Medium"
    }
}

def get_routing_info(issue_type):
    """
    Returns the department and priority for a given issue type.
    Defaults to 'Unassigned' and 'Low' priority if type is unknown.
    """
    # Normalize input
    issue_type = str(issue_type).lower().strip()
    
    return DEPARTMENT_RULES.get(issue_type, {
        "dept": "Unassigned", 
        "priority": "Low"
    })
