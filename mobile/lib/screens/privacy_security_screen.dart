/// Privacy & Security - static informational screen.
library;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class PrivacySecurityScreen extends StatelessWidget {
  const PrivacySecurityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Privacy & Security')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          _Section(
            icon: Icons.visibility_off_outlined,
            title: 'Your data stays private',
            body:
                'UrbanEye only stores what is needed to resolve your reports: '
                'your name, email and the issue photos you submit. Your exact '
                'home address is never stored or shown publicly.',
          ),
          _Section(
            icon: Icons.shield_outlined,
            title: 'Secure sign-in',
            body:
                'Passwords are hashed and never sent back to clients. Your '
                'session token is kept only on your device, inside secure '
                'app storage (SharedPreferences).',
          ),
          _Section(
            icon: Icons.location_off_outlined,
            title: 'Location used only for reports',
            body:
                'GPS is requested only when you actively report an issue, so '
                'civic workers know where to go. Your location is never '
                'tracked in the background.',
          ),
          _Section(
            icon: Icons.image_outlined,
            title: 'Report photos',
            body:
                'Photos are compressed before upload and attached to a single '
                'report. They are never shared to third parties or shown on '
                'the public map without a report.',
          ),
          _Section(
            icon: Icons.delete_outline,
            title: 'Delete your data',
            body:
                'To remove your account and all associated reports, contact '
                'support at support@urbaneye.app with the email you registered. '
                'Requests are processed within 7 days.',
          ),
          _Section(
            icon: Icons.campaign_outlined,
            title: 'No spam, ever',
            body:
                'Notifications are opt-in per report. We do not send marketing '
                'messages, and a weekly summary can always be turned off from '
                'the Notifications screen.',
          ),
          SizedBox(height: 16),
          Center(
            child: Text(
              'UrbanEye app · v1.0',
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  const _Section({required this.icon, required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: const Color(0xFF0D47A1)),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title,
                    style: GoogleFonts.inter(
                        fontSize: 15, fontWeight: FontWeight.w700)),
                const SizedBox(height: 4),
                Text(body,
                    style: GoogleFonts.inter(
                        fontSize: 13,
                        height: 1.4,
                        color: Colors.grey.shade800)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}