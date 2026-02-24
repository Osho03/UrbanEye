try:
    import cv2
    print("✅ OpenCV imported successfully")
except ImportError as e:
    print(f"❌ OpenCV Import Error: {e}")
except Exception as e:
    print(f"❌ OpenCV Other Error: {e}")
