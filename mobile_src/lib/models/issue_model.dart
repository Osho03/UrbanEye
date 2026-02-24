/// Issue model for UrbanEye
import 'dart:ui';

class Issue {
  final String? issueId;
  final String? title;
  final String? description;
  final String? issueType;
  final String? status;
  final String? latitude;
  final String? longitude;
  final String? address;
  final String? imagePath;
  final String? reportedBy;
  final String? reporterEmail;
  final String? assignedDepartment;
  final String? priority;
  final String? severityLabel;
  final int? severityScore;
  final String? adminRemarks;
  final String? mediaType;
  final String? createdAt;
  final String? updatedAt;
  final int? supportCount;
  final List<StatusHistoryEntry>? statusHistory;

  Issue({
    this.issueId,
    this.title,
    this.description,
    this.issueType,
    this.status,
    this.latitude,
    this.longitude,
    this.address,
    this.imagePath,
    this.reportedBy,
    this.reporterEmail,
    this.assignedDepartment,
    this.priority,
    this.severityLabel,
    this.severityScore,
    this.adminRemarks,
    this.mediaType,
    this.createdAt,
    this.updatedAt,
    this.supportCount,
    this.statusHistory,
  });

  factory Issue.fromJson(Map<String, dynamic> json) {
    return Issue(
      issueId: json['issue_id'] as String?,
      title: json['title'] as String?,
      description: json['description'] as String?,
      issueType: _parseIssueType(json['issue_type']),
      status: json['status'] as String?,
      latitude: json['latitude']?.toString(),
      longitude: json['longitude']?.toString(),
      address: json['address'] as String?,
      imagePath: json['image_path'] as String?,
      reportedBy: json['reported_by'] as String?,
      reporterEmail: json['reporter_email'] as String?,
      assignedDepartment: json['assigned_department'] as String?,
      priority: json['priority'] as String?,
      severityLabel: json['severity_label'] as String?,
      severityScore: json['severity_score'] as int?,
      adminRemarks: json['admin_remarks'] as String?,
      mediaType: json['media_type'] as String?,
      createdAt: json['created_at']?.toString(),
      updatedAt: json['updated_at']?.toString(),
      supportCount: json['support_count'] as int?,
      statusHistory: (json['status_history'] as List<dynamic>?)
          ?.map((e) => StatusHistoryEntry.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }

  static String? _parseIssueType(dynamic issueType) {
    if (issueType is String) return issueType;
    if (issueType is Map) {
      return (issueType['detected_type'] ?? issueType['primary_guess'] ?? 'Unknown') as String;
    }
    return 'Unknown';
  }

  Color get statusColor {
    switch (status?.toLowerCase()) {
      case 'pending':
        return const Color(0xFFFFA726);
      case 'assigned':
        return const Color(0xFF42A5F5);
      case 'in progress':
        return const Color(0xFF7E57C2);
      case 'resolved':
        return const Color(0xFF66BB6A);
      case 'duplicate':
        return const Color(0xFFEF5350);
      default:
        return const Color(0xFF9E9E9E);
    }
  }

  String get displayIssueType {
    if (issueType == null || issueType!.isEmpty) return 'Unknown';
    return issueType!.replaceAll('_', ' ').split(' ').map((word) {
      if (word.isEmpty) return word;
      return word[0].toUpperCase() + word.substring(1).toLowerCase();
    }).join(' ');
  }
}

class StatusHistoryEntry {
  final String? oldStatus;
  final String? newStatus;
  final String? changedAt;
  final String? changedBy;
  final String? comment;

  StatusHistoryEntry({
    this.oldStatus,
    this.newStatus,
    this.changedAt,
    this.changedBy,
    this.comment,
  });

  factory StatusHistoryEntry.fromJson(Map<String, dynamic> json) {
    return StatusHistoryEntry(
      oldStatus: json['old_status'] as String?,
      newStatus: json['new_status'] ?? json['status'] as String?,
      changedAt: json['changed_at']?.toString(),
      changedBy: json['changed_by'] as String?,
      comment: json['comment'] as String?,
    );
  }
}
