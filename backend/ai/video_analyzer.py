"""
Video Analyzer for UrbanEye AI (Mock Implementation)
Handles video processing when OpenCV is unavailable.
"""

def process_video(video_path):
    """
    Mock implementation of video analysis.
    Returns a safe default value since CV2 is unavailable.
    """
    print(f"⚠️ Video Analysis: OpenCV unavailable. Skipping analysis for {video_path}")
    return "unknown"
