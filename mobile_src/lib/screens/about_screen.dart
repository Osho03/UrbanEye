/// About UrbanEye - static informational screen.
library;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('About UrbanEye')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF0D47A1), Color(0xFF00897B)],
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.location_city,
                      size: 40, color: Color(0xFF0D47A1)),
                ),
                const SizedBox(height: 12),
                Text('UrbanEye',
                    style: GoogleFonts.inter(
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                        color: Colors.white)),
                const Text('v1.0.0',
                    style: TextStyle(color: Colors.white70, fontSize: 13)),
                const SizedBox(height: 8),
                Text(
                  'Your city, in your hands. Report civic issues in seconds '
                  'and track them until they are resolved.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                      fontSize: 13, color: Colors.white, height: 1.4),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          const _Feature(
            icon: Icons.camera_alt_outlined,
            title: 'Report in seconds',
            body:
                'Snap a photo or use voice-to-text, drop a pin and describe '
                'the issue. UrbanEye routes it to the right department.',
          ),
          const _Feature(
            icon: Icons.hub_outlined,
            title: 'AI-assisted routing',
            body:
                'Machine-learning models classify issue type and severity so '
                'urgent problems get priority attention.',
          ),
          const _Feature(
            icon: Icons.timeline_outlined,
            title: 'Live tracking',
            body:
                'Watch your report move through under review, in progress and '
                'resolved - and get notified the moment it changes.',
          ),
          const _Feature(
            icon: Icons.workspaces_outline,
            title: 'Backed by data',
            body:
                'Trends, seasonal patterns and predictive maintenance help '
                'your city act before problems grow.',
          ),
          const SizedBox(height: 12),
          const Center(
            child: Text(
              'Modern Civic Problem Reporting for Smart Cities',
              style: TextStyle(color: Colors.grey, fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }
}

class _Feature extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  const _Feature({required this.icon, required this.title, required this.body});

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