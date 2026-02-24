/// Issue Detail Screen - Full details + AI Summary (backend-powered)
/// All AI operations are processed by the Flask backend.
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../models/issue_model.dart';
import '../services/api_service.dart';

class IssueDetailScreen extends StatefulWidget {
  final Issue issue;

  const IssueDetailScreen({super.key, required this.issue});

  @override
  State<IssueDetailScreen> createState() => _IssueDetailScreenState();
}

class _IssueDetailScreenState extends State<IssueDetailScreen> {
  Map<String, dynamic>? _aiSummary;
  bool _loadingSummary = false;

  Future<void> _fetchAISummary() async {
    if (widget.issue.issueId == null) return;
    setState(() => _loadingSummary = true);
    try {
      final result = await ApiService.getAISummary(widget.issue.issueId!);
      if (mounted) {
        setState(() {
          _aiSummary = result;
          _loadingSummary = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _aiSummary = {'error': 'Failed to load: $e'};
          _loadingSummary = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final issue = widget.issue;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Issue Details'),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Hero Image
            if (issue.imagePath != null)
              SizedBox(
                height: 250,
                child: Image.network(
                  ApiService.getImageUrl(issue.imagePath),
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    color: Colors.grey.shade200,
                    child: const Center(
                      child: Icon(Icons.image_not_supported,
                          size: 48, color: Colors.grey),
                    ),
                  ),
                ),
              ),

            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title & Status
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          issue.title ?? 'Untitled Issue',
                          style: GoogleFonts.inter(
                              fontSize: 22, fontWeight: FontWeight.w700),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 14, vertical: 8),
                        decoration: BoxDecoration(
                          color: issue.statusColor,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          issue.status ?? 'Unknown',
                          style: GoogleFonts.inter(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 20),

                  // Info Grid
                  _InfoTile(
                    icon: Icons.category_outlined,
                    label: 'Issue Type',
                    value: issue.displayIssueType,
                  ),
                  _InfoTile(
                    icon: Icons.business,
                    label: 'Department',
                    value: issue.assignedDepartment ?? 'Unassigned',
                  ),
                  _InfoTile(
                    icon: Icons.priority_high,
                    label: 'Priority',
                    value: issue.priority ?? 'Normal',
                  ),
                  if (issue.severityLabel != null)
                    _InfoTile(
                      icon: Icons.warning_amber_outlined,
                      label: 'Severity',
                      value:
                          '${issue.severityLabel} (${issue.severityScore ?? 0}/10)',
                    ),
                  if (issue.address != null)
                    _InfoTile(
                      icon: Icons.location_on_outlined,
                      label: 'Location',
                      value: issue.address!,
                    ),
                  if (issue.latitude != null && issue.longitude != null)
                    _InfoTile(
                      icon: Icons.gps_fixed,
                      label: 'GPS',
                      value: '${issue.latitude}, ${issue.longitude}',
                    ),
                  if (issue.createdAt != null)
                    _InfoTile(
                      icon: Icons.access_time,
                      label: 'Reported',
                      value: _formatDate(issue.createdAt!),
                    ),

                  // Description
                  const SizedBox(height: 20),
                  Text(
                    'Description',
                    style: GoogleFonts.inter(
                        fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: Text(
                      issue.description ?? 'No description provided',
                      style: GoogleFonts.inter(
                          fontSize: 14,
                          height: 1.6,
                          color: Colors.grey.shade700),
                    ),
                  ),

                  // ── AI Summary (Backend-Powered) ──
                  const SizedBox(height: 20),
                  _buildAISummarySection(),

                  // Admin Remarks
                  if (issue.adminRemarks != null &&
                      issue.adminRemarks!.isNotEmpty) ...[
                    const SizedBox(height: 20),
                    Text(
                      'Admin Remarks',
                      style: GoogleFonts.inter(
                          fontSize: 16, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.blue.shade50,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.blue.shade100),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.admin_panel_settings,
                              size: 20, color: Colors.blue.shade700),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              issue.adminRemarks!,
                              style: GoogleFonts.inter(
                                  fontSize: 14, color: Colors.blue.shade800),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],

                  // Status Timeline
                  if (issue.statusHistory != null &&
                      issue.statusHistory!.isNotEmpty) ...[
                    const SizedBox(height: 24),
                    Text(
                      'Status Timeline',
                      style: GoogleFonts.inter(
                          fontSize: 16, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 12),
                    ...issue.statusHistory!.asMap().entries.map((entry) {
                      final idx = entry.key;
                      final historyEntry = entry.value;
                      final isLast = idx == issue.statusHistory!.length - 1;
                      return _TimelineItem(
                        entry: historyEntry,
                        isLast: isLast,
                        isFirst: idx == 0,
                      );
                    }),
                  ],

                  const SizedBox(height: 30),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// AI Summary section — fetches summary from backend on demand
  Widget _buildAISummarySection() {
    if (_aiSummary != null) {
      // Show the result
      final hasError = _aiSummary!.containsKey('error');
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: hasError
              ? null
              : const LinearGradient(
                  colors: [Color(0xFFe8eaf6), Color(0xFFf3e5f5)],
                ),
          color: hasError ? Colors.red.shade50 : null,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: hasError ? Colors.red.shade200 : Colors.purple.shade100),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  hasError ? Icons.error_outline : Icons.auto_awesome,
                  size: 20,
                  color: hasError ? Colors.red : Colors.purple.shade700,
                ),
                const SizedBox(width: 8),
                Text(
                  hasError ? 'AI Summary Error' : '🤖 AI Inspection Summary',
                  style: GoogleFonts.inter(
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                    color: hasError ? Colors.red : Colors.purple.shade800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              hasError
                  ? _aiSummary!['error'].toString()
                  : _aiSummary!['summary']?.toString() ??
                      _aiSummary!['inspection_summary']?.toString() ??
                      _aiSummary.toString(),
              style: GoogleFonts.inter(
                fontSize: 14,
                height: 1.5,
                color: hasError ? Colors.red.shade700 : Colors.grey.shade800,
              ),
            ),
            if (!hasError && _aiSummary!['recommendation'] != null) ...[
              const SizedBox(height: 10),
              Text(
                '💡 ${_aiSummary!['recommendation']}',
                style: GoogleFonts.inter(
                  fontSize: 13,
                  fontStyle: FontStyle.italic,
                  color: Colors.purple.shade600,
                ),
              ),
            ],
          ],
        ),
      );
    }

    // Show the "Get AI Summary" button
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: _loadingSummary ? null : _fetchAISummary,
        icon: _loadingSummary
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2))
            : const Icon(Icons.auto_awesome),
        label: Text(
          _loadingSummary ? 'Generating AI Summary...' : '🤖 Get AI Summary',
          style: GoogleFonts.inter(fontWeight: FontWeight.w600),
        ),
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.purple.shade700,
          side: BorderSide(color: Colors.purple.shade300),
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final dt = DateTime.parse(dateStr);
      return DateFormat('MMM dd, yyyy • hh:mm a').format(dt);
    } catch (_) {
      return dateStr;
    }
  }
}

class _InfoTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoTile(
      {required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey.shade500),
          const SizedBox(width: 12),
          SizedBox(
            width: 90,
            child: Text(label,
                style: GoogleFonts.inter(
                    fontSize: 13, color: Colors.grey.shade500)),
          ),
          Expanded(
            child: Text(value,
                style: GoogleFonts.inter(
                    fontSize: 14, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}

class _TimelineItem extends StatelessWidget {
  final StatusHistoryEntry entry;
  final bool isLast;
  final bool isFirst;

  const _TimelineItem(
      {required this.entry, required this.isLast, required this.isFirst});

  @override
  Widget build(BuildContext context) {
    final statusText = entry.newStatus ?? entry.oldStatus ?? 'Unknown';
    Color dotColor;
    switch (statusText.toLowerCase()) {
      case 'pending':
        dotColor = const Color(0xFFFFA726);
        break;
      case 'assigned':
        dotColor = const Color(0xFF42A5F5);
        break;
      case 'in progress':
        dotColor = const Color(0xFF7E57C2);
        break;
      case 'resolved':
        dotColor = const Color(0xFF66BB6A);
        break;
      default:
        dotColor = const Color(0xFF9E9E9E);
    }

    String dateStr = '';
    if (entry.changedAt != null) {
      try {
        final dt = DateTime.parse(entry.changedAt!);
        dateStr = DateFormat('MMM dd, hh:mm a').format(dt);
      } catch (_) {
        dateStr = entry.changedAt ?? '';
      }
    }

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Timeline line + dot
          SizedBox(
            width: 32,
            child: Column(
              children: [
                Container(
                  width: 14,
                  height: 14,
                  decoration: BoxDecoration(
                    color: dotColor,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                    boxShadow: [
                      BoxShadow(color: dotColor.withOpacity(0.3), blurRadius: 4)
                    ],
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: Colors.grey.shade300,
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Content
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    statusText,
                    style: GoogleFonts.inter(
                        fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  if (entry.changedBy != null)
                    Text(
                      'by ${entry.changedBy}',
                      style:
                          GoogleFonts.inter(fontSize: 12, color: Colors.grey),
                    ),
                  if (dateStr.isNotEmpty)
                    Text(
                      dateStr,
                      style: GoogleFonts.inter(
                          fontSize: 11, color: Colors.grey.shade400),
                    ),
                  if (entry.comment != null && entry.comment!.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      entry.comment!,
                      style: GoogleFonts.inter(
                          fontSize: 13, color: Colors.grey.shade600),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
