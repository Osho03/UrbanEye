# UrbanEye Mobile App (Flutter)

Flutter-based Android mobile client for the UrbanEye Citizen Reporting System.

## Prerequisites

1. **Flutter SDK** — Install from [flutter.dev](https://flutter.dev/docs/get-started/install)
2. **Android Studio** or **VS Code** with Flutter extension
3. **UrbanEye Backend** running on `localhost:5000`

## Quick Start

```bash
# 1. Navigate to mobile directory
cd d:\UrbanEye\mobile

# 2. Install dependencies
flutter pub get

# 3. Run on emulator or connected device
flutter run
```

## Server Configuration

- **Android Emulator**: Default URL is `http://10.0.2.2:5000` (maps to host's localhost)
- **Physical Device**: Change the server URL in Profile → Server Settings to your PC's local IP (e.g., `http://192.168.1.100:5000`)
- Make sure the Flask backend is running: `cd d:\UrbanEye\backend && python app.py`

## Features

| Feature | Plugin | Status |
|---------|--------|--------|
| 📸 Camera Capture | `image_picker` | ✅ |
| 📍 GPS Location | `geolocator` + `geocoding` | ✅ |
| 🎤 Voice Input | `speech_to_text` | ✅ |
| 🗺️ Map View | `flutter_map` (OpenStreetMap) | ✅ |
| 📦 Image Compression | `flutter_image_compress` | ✅ |
| 🔐 User Auth | Backend API + SharedPreferences | ✅ |
| 📋 My Reports | User-specific filtering | ✅ |
| 📊 Status Tracking | Timeline view | ✅ |

## Project Structure

```
mobile/
├── lib/
│   ├── main.dart                 # App entry point + theme
│   ├── models/
│   │   ├── issue_model.dart      # Issue data model
│   │   └── user_model.dart       # User data model
│   ├── services/
│   │   ├── api_service.dart      # Backend API client
│   │   └── auth_service.dart     # Auth state management
│   └── screens/
│       ├── login_screen.dart     # Login / Register
│       ├── home_screen.dart      # Dashboard
│       ├── report_screen.dart    # Report an issue
│       ├── my_reports_screen.dart # User's reports
│       ├── issue_detail_screen.dart # Issue details + timeline
│       ├── map_screen.dart       # Map view
│       └── profile_screen.dart   # User profile
├── android/
│   └── app/src/main/AndroidManifest.xml  # Permissions
└── pubspec.yaml                  # Dependencies
```

## Backend Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/user/register` | POST | User registration |
| `/api/user/login` | POST | User login |
| `/api/user/profile/<id>` | GET/PUT | Profile view/edit |
| `/api/user/reports/<id>` | GET | User's reports |
| `/api/issues/report` | POST | Submit issue (multipart) |
| `/api/issues/all` | GET | All issues (for map) |
| `/api/issues/<id>/status` | GET | Issue status |
| `/api/analytics/stats` | GET | Dashboard stats |

## Build APK

```bash
flutter build apk --release
```

The APK will be at `build/app/outputs/flutter-apk/app-release.apk`
