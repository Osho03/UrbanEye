/// Firebase Cloud Messaging - true push notifications.
///
/// Registers the device token with the UrbanEye backend when the citizen logs
/// in. When an admin updates a report's status, the backend FCM-pushes to the
/// reporter's device - notifications arrive even when the app is closed.
///
/// Requires `android/app/google-services.json` (generated in the Firebase
/// console for package com.urbaneye.app) and a Firebase Realtime/Database-free
/// project. The backend sends via the Firebase Admin SDK (service account).
library;
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import 'notification_service.dart';

class FcmService {
  FcmService._();
  static final FcmService instance = FcmService._();

  bool _initialized = false;
  String _userId = '';
  String? _token;

  bool get isReady => _initialized;

  /// Initialise Firebase + obtain the device token. Safe to call at startup;
  /// silently no-ops if google-services.json is absent.
  Future<void> init() async {
    try {
      await Firebase.initializeApp();
      _initialized = true;
    } catch (e) {
      debugPrint('FCM init skipped: $e');
      return;
    }

    final messaging = FirebaseMessaging.instance;

    // Android 13+ runtime permission
    final settings = await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: true,
    );
    debugPrint('FCM permission granted: ${settings.authorizationStatus}');

    // Headless token refresh -> re-register with backend
    messaging.onTokenRefresh.listen((token) async {
      _token = token;
      if (_userId.isNotEmpty) {
        await registerToken(_userId);
      }
    });

    // Foreground messages: show a local notification ourselves
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      _renderMessage(message);
    });
  }

  /// Store which citizen this device belongs to and register the token.
  Future<void> registerToken(String userId) async {
    _userId = userId;
    if (!_initialized) return;
    final token = _token ?? await FirebaseMessaging.instance.getToken();
    if (token == null) {
      return;
    }
    _token = token;
    await ApiService.registerFcmToken(userId: userId, token: token);
  }

  void _renderMessage(RemoteMessage message) {
    final data = message.data;
    final status = (data['status'] as String?) ?? 'updated';
    final title = (message.notification?.title) ??
        'UrbanEye · ${_pretty(status)}';
    final body = (message.notification?.body) ??
        (data['issue_title'] as String? ?? 'Your report was updated');
    NotificationService.instance.showLocal(title, body);
    // Persist last-seen so the poller doesn't re-notify the same update.
    final changedAt = data['changed_at'] as String?;
    if (changedAt != null && changedAt.isNotEmpty) {
      SharedPreferences.getInstance().then((prefs) =>
          prefs.setString('last_seen_notif_at', changedAt.toLowerCase()));
    }
  }

  String _pretty(String status) {
    return status.replaceAll('_', ' ').toUpperCase();
  }
}