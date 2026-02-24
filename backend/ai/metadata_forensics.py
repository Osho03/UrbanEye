from PIL import Image, ExifTags
from datetime import datetime, timedelta
import os

def analyze_metadata(image_path):
    """
    Extract EXIF metadata to determine if an image is 'Fresh' or 'Stale'.
    
    Returns:
        dict: {
            "status": "Fresh" | "Stale" | "Unknown",
            "capture_time": str | None,
            "report_time": str,
            "age_hours": float | None,
            "details": str
        }
    """
    try:
        report_time = datetime.now()
        
        if not os.path.exists(image_path):
             return {
                "status": "Error",
                "details": "Image file not found on server"
            }
            
        if os.path.getsize(image_path) == 0:
             return {
                "status": "Error",
                "details": "Uploaded file is empty (0 bytes)"
            }

        img = Image.open(image_path)
        exif_data = img._getexif()
        
        if not exif_data:
            return {
                "status": "Unknown",
                "capture_time": None,
                "report_time": report_time.strftime("%Y-%m-%d %H:%M:%S"),
                "age_hours": None,
                "details": "No EXIF metadata found (Metadata stripped or screenshot)"
            }
            
        # Find DateTimeOriginal (Tag 36867)
        date_taken_str = None
        for tag, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag, tag)
            if tag_name == "DateTimeOriginal":
                date_taken_str = value
                break
                
        if not date_taken_str:
            return {
                "status": "Unknown",
                "capture_time": None,
                "report_time": report_time.strftime("%Y-%m-%d %H:%M:%S"),
                "age_hours": None,
                "details": "No 'Date Taken' timestamp in metadata"
            }
            
        # Parse Date (Format: YYYY:MM:DD HH:MM:SS)
        try:
            capture_time = datetime.strptime(date_taken_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
             return {
                "status": "Unknown",
                "capture_time": date_taken_str,
                "report_time": report_time.strftime("%Y-%m-%d %H:%M:%S"),
                "age_hours": None,
                "details": "Unrecognized date format in metadata"
            }
            
        # Calculate Age
        age = report_time - capture_time
        age_hours = age.total_seconds() / 3600
        
        # Fraud Logic: If photo is older than 24 hours
        if age_hours > 24:
            return {
                "status": "Stale",
                "capture_time": str(capture_time),
                "report_time": str(report_time),
                "age_hours": round(age_hours, 1),
                "details": f"Photo is {round(age_hours, 1)} hours old (>24h limit)"
            }
        
        # If capture time is effectively in the future (permitting small clock skew)
        if age_hours < -1: 
             return {
                "status": "Suspicious",
                "capture_time": str(capture_time),
                "report_time": str(report_time),
                "age_hours": round(age_hours, 1),
                "details": "Future timestamp detected (Clock manipulation?)"
            }

        return {
            "status": "Fresh",
            "capture_time": str(capture_time),
            "report_time": str(report_time),
            "age_hours": round(age_hours, 1),
            "details": "Verified recent capture"
        }

    except Exception as e:
        print(f"Forensics Error: {e}")
        return {
            "status": "Error",
            "details": str(e)
        }
