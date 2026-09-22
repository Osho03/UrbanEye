/// Real-time notification service for UrbanEye.
///
/// Polls the backend for status updates on the user's reports and fires
/// OS-level notifications (flutter_local_notifications) when new ones arrive.
/// This works without Firebase; to upgrade to true push (app closed) see the
/// Firebase Cloud Messaging (FCM) steps documented in the README/help.
library;
import 'dart:async';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  Timer? _timer;
  String _lastSeen = '';
  String _userId = '';

  static const _channel = AndroidNotificationDetails(
    'urbaneye_status',
    'Report Status Updates',
    channelDescription: 'Alerts when your UrbanEye report status changes',
    importance: Importance.high,
    priority: Priority.high,
    icon: '@mipmap/ic_launcher',
  );

  /// Setup the plugin + Android permission. Call once at app start.
  Future<void> init() async {
    const android =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const settings = InitializationSettings(android: android);
    await _plugin.initialize(settings: settings);

    final prefs = await SharedPreferences.getInstance();
    _lastSeen = prefs.getString('last_seen_notif_at') ?? '';

    // Android 13+ runtime notification permission
    final androidImpl = _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    await androidImpl?.requestNotificationsPermission();
  }

  /// Start checking every [seconds] for new updates (only when logged in
  /// and notifications are enabled). Real-time via lightweight polling.
  void start({String userId = '', Duration interval = const Duration(seconds: 30)}) {
    if (userId.isNotEmpty) _userId = userId;
    _timer?.cancel();
    _timer = Timer.periodic(interval, (_) => checkNow());
  }

  void stop() {
    _timer?.cancel();
    _timer = null;
  }

  /// One check against the backend. Returns the list of brand-new items.
  Future<List<Map<String, dynamic>>> checkNow({String? userId}) async {
    final id = userId ?? _userId;
    if (id.isEmpty) return [];

    List<Map<String, dynamic>> items;
    try {
      items = await ApiService.getUserNotifications(id);
    } catch (e) {
      return [];
    }

    final fresh = <Map<String, dynamic>>[];
    for (final item in items) {
      final ts = (item['changed_at'] as String? ?? '').toLowerCase();
      if (ts.isEmpty) continue;
      if (_lastSeen.isEmpty || ts.compareTo(_lastSeen) > 0) {
        fresh.add(item);
      }
    }

    if (fresh.isNotEmpty) {
      _lastSeen = items.first['changed_at'] as String? ?? _lastSeen;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('last_seen_notif_at', _lastSeen);
      for (final item in fresh.reversed) {
        _show(item);
      }
      return fresh;
    }
    return [];
  }

  /// Fire a plain local notification (used by FCM foreground messages).
  Future<void> showLocal(String title, String body) async {
    await _plugin.show(
      id: (title + body).hashCode,
      title: title,
      body: body,
      notificationDetails: const NotificationDetails(android: _channel),
    );
  }

  Future<void> _show(Map<String, dynamic> item) async {
    final status = (item['status'] as String? ?? 'Updated');
    final title = (item['issue_title'] as String? ?? 'Your report');
    await _plugin.show(
      id: item.hashCode,
      title: 'UrbanEye · $status',
      body: title.isEmpty ? 'Your report was updated' : title,
      notificationDetails: const NotificationDetails(android: _channel),
    );
  }
}