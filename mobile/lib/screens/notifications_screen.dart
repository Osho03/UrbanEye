/// Notifications screen - preferences + live status-update feed.
library;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/notification_service.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool _enabled = true;
  bool _statusUpdates = true;
  bool _digest = false;
  bool _loading = true;
  bool _saving = false;
  List<Map<String, dynamic>> _feed = [];

  @override
  void initState() {
    super.initState();
    final auth = Provider.of<AuthService>(context, listen: false);
    final u = auth.currentUser;
    _enabled = u?.notificationsEnabled ?? true;
    _statusUpdates = u?.notifyStatusUpdates ?? true;
    _digest = u?.notifyDigest ?? false;
    NotificationService.instance.start();
    _load();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _load() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    final items = await ApiService.getUserNotifications(auth.userId);
    if (mounted) {
      setState(() {
        _feed = items;
        _loading = false;
      });
    }
  }

  Future<void> _persist() async {
    final auth = Provider.of<AuthService>(context, listen: false);
    setState(() => _saving = true);
    try {
      await ApiService.updateProfile(
        auth.userId,
        notificationsEnabled: _enabled,
        notifyStatusUpdates: _statusUpdates,
        notifyDigest: _digest,
      );
      await auth.updateLocalUser(
        notificationsEnabled: _enabled,
        notifyStatusUpdates: _statusUpdates,
        notifyDigest: _digest,
      );
      // Keep the poller in sync with the master switch.
      if (_enabled) {
        NotificationService.instance.start();
      } else {
        NotificationService.instance.stop();
      }
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Preferences saved')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not save preferences')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          _saving
              ? const Padding(
                  padding: EdgeInsets.all(16),
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : TextButton(
                  onPressed: _persist,
                  child: const Text('Save',
                      style: TextStyle(fontWeight: FontWeight.w600)),
                ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF0D47A1), Color(0xFF00897B)],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.notifications_active,
                          color: Colors.white, size: 32),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Real-time alerts',
                          style: GoogleFonts.inter(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                              color: Colors.white),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'You will be notified the moment an authority updates the '
                    'status of your report-submitted issues.',
                    style: GoogleFonts.inter(
                        fontSize: 13, color: Colors.white70),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              value: _enabled,
              onChanged: (v) => setState(() => _enabled = v),
              title: const Text('Enable notifications'),
              subtitle: const Text('Master switch for all alerts'),
            ),
            SwitchListTile(
              value: _statusUpdates,
              onChanged: (v) => setState(() => _statusUpdates = v),
              title: const Text('Status update alerts'),
              subtitle: const Text('When a report moves to in progress / resolved'),
            ),
            SwitchListTile(
              value: _digest,
              onChanged: (v) => setState(() => _digest = v),
              title: const Text('Weekly summary'),
              subtitle: const Text('Digest of your city impact each week'),
            ),
            const Divider(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Activity feed',
                    style: GoogleFonts.inter(
                        fontSize: 16, fontWeight: FontWeight.w700)),
                IconButton(
                  icon: const Icon(Icons.check_circle_outline),
                  tooltip: 'Mark all seen',
                  onPressed: () async {
                    await NotificationService.instance.checkNow(
                        userId:
                            Provider.of<AuthService>(context, listen: false)
                                .userId);
                    await _load();
                  },
                ),
              ],
            ),
            const SizedBox(height: 4),
            if (_loading)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 40),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_feed.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 40),
                child: Column(
                  children: [
                    Icon(Icons.notifications_off_outlined,
                        size: 48, color: Colors.grey.shade400),
                    const SizedBox(height: 8),
                    Text('No updates yet',
                        style: GoogleFonts.inter(
                            color: Colors.grey, fontWeight: FontWeight.w600)),
                    Text('Your report status changes will appear here.',
                        style: GoogleFonts.inter(
                            color: Colors.grey, fontSize: 12)),
                  ],
                ),
              )
            else
              ..._feed.map((n) => _NotificationTile(item: n)),
          ],
        ),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final Map<String, dynamic> item;
  const _NotificationTile({required this.item});

  @override
  Widget build(BuildContext context) {
    final status = (item['status'] as String? ?? 'updated').toLowerCase();
    Color color;
    IconData icon;
    switch (status) {
      case 'resolved':
        color = Colors.green;
        icon = Icons.check_circle;
        break;
      case 'in_progress':
        color = Colors.orange;
        icon = Icons.pending;
        break;
      case 'under_review':
        color = Colors.blue;
        icon = Icons.visibility;
        break;
      default:
        color = Colors.teal;
        icon = Icons.update;
    }
    final ts = item['changed_at'] as String? ?? '';
    final when = ts.length >= 16
        ? '${ts.substring(0, 16).replaceAll('T', ' ')}'
        : ts;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
Text(
                      status.replaceAll('_', ' ').toUpperCase(),
                  style: GoogleFonts.inter(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: color),
                ),
                const SizedBox(height: 2),
                Text(item['issue_title'] as String? ?? 'Your report',
                    style: GoogleFonts.inter(
                        fontSize: 14, fontWeight: FontWeight.w600)),
                if ((item['comment'] as String? ?? '').isNotEmpty)
                  Text(item['comment'] as String,
                      style: GoogleFonts.inter(
                          fontSize: 12, color: Colors.grey)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(when,
                        style: GoogleFonts.inter(
                            fontSize: 11, color: Colors.grey)),
                    const SizedBox(width: 8),
                    Text('· by ${item['changed_by'] ?? 'System'}',
                        style: GoogleFonts.inter(
                            fontSize: 11, color: Colors.grey)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}