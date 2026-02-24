import cv2
import numpy as np

def estimate_severity(image_path, issue_type):
    """
    Estimate the severity of a civic issue (1-10 scale).
    
    Logic:
    1. Base Score: Dependent on Issue Type (e.g., Pothole=5, Garbage=3).
    2. Visual Modifier:
       - Edge Density: More edges = more cracks/complexity (+0 to +2).
       - Contrast: Higher contrast = deeper shadows/holes (+0 to +2).
       
    Returns:
        dict: { "score": int, "label": str, "details": dict }
    """
    try:
        # 1. Base Score Rules
        base_scores = {
            "pothole": 5,
            "water_leak": 7,  # Water is urgent
            "garbage": 3,
            "streetlight": 4,
            "unknown": 1
        }
        base = base_scores.get(str(issue_type).lower(), 3)
        if str(issue_type).startswith("Advisory"): # For video
            base = 5
            
        # 2. Visual Analysis
        img = cv2.imread(image_path)
        if img is None:
            return {"score": base, "label": get_label(base), "details": {"method": "base_only"}}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # A. Edge Density (Canny) -> Complexity
        edges = cv2.Canny(gray, 100, 200)
        edge_ratio = np.count_nonzero(edges) / edges.size
        edge_modifier = 0
        if edge_ratio > 0.15: edge_modifier = 2
        elif edge_ratio > 0.05: edge_modifier = 1
        
        # B. Contrast (RMS) -> Depth/Shadows
        contrast = gray.std()
        contrast_modifier = 0
        if contrast > 60: contrast_modifier = 2
        elif contrast > 40: contrast_modifier = 1
        
        # 3. Final Calculation
        final_score = base + edge_modifier + contrast_modifier
        
        # Clamp to 1-10
        final_score = max(1, min(10, final_score))
        
        return {
            "score": final_score,
            "label": get_label(final_score),
            "details": {
                "base": base,
                "edge_mod": edge_modifier,
                "contrast_mod": contrast_modifier
            }
        }
        
    except Exception as e:
        print(f"Error estimating severity: {e}")
        return {"score": 1, "label": "Low", "details": {"error": str(e)}}

def get_label(score):
    if score >= 8: return "Critical"
    if score >= 6: return "High"
    if score >= 4: return "Medium"
    return "Low"
