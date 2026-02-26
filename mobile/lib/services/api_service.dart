/// ============================================================
/// API Service for UrbanEye — Client-Only Architecture
/// ============================================================
/// Flutter is a PURE CLIENT INTERFACE.
/// All AI operations (classification, chatbot, summarization,
/// prediction) are handled by the Flask Backend.
/// Flutter sends requests ONLY to backend endpoints.
/// NO AI API keys or AI logic exists in Flutter.
/// ============================================================
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:mime/mime.dart';
import '../models/issue_model.dart';

class ApiService {
  static String baseUrl = kIsWeb
      ? 'http://localhost:5000'
      : 'https://urbaneye-backend-kzb6.onrender.com';

  /// Configure base URL (call from settings)
  static void setBaseUrl(String url) {
    baseUrl = url;
  }

  // ==================== HEALTH ====================

  static Future<bool> healthCheck() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/health'))
          .timeout(const Duration(seconds: 10)); // Increased timeout

      final isOk = response.statusCode == 200;
      if (!isOk) {
        debugPrint('⚠️ Health check returned non-200: ${response.statusCode}');
      }
      return isOk;
    } catch (e) {
      debugPrint('❌ Health check error: $e');
      return false;
    }
  }

  // ==================== AUTH ====================

  static Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
    String? phone,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/user/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': name,
        'email': email,
        'password': password,
        'phone': phone ?? '',
      }),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/user/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> getProfile(String userId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/user/profile/$userId'),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> updateProfile(
    String userId, {
    String? name,
    String? phone,
  }) async {
    final body = <String, dynamic>{};
    if (name != null) body['name'] = name;
    if (phone != null) body['phone'] = phone;

    final response = await http.put(
      Uri.parse('$baseUrl/api/user/profile/$userId'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return jsonDecode(response.body);
  }

  // ==================== ISSUES ====================

  /// Report a new issue — sends image as multipart/form-data with GPS coordinates.
  /// Backend handles ALL AI processing (classification, routing, severity).
  /// Works on both web and mobile (uses Uint8List, not dart:io File).
  static Future<Map<String, dynamic>> reportIssueBytes({
    required Uint8List imageBytes,
    required String fileName,
    required String title,
    required String description,
    required String latitude,
    required String longitude,
    String? address,
    required String reportedBy,
    String? reporterEmail,
    String? voiceTranscript,
  }) async {
    final uri = Uri.parse('$baseUrl/api/issues/report');
    final request = http.MultipartRequest('POST', uri);

    // Image as multipart/form-data
    final mimeType = lookupMimeType(fileName) ?? 'image/jpeg';
    final mimeTypeParts = mimeType.split('/');
    request.files.add(
      http.MultipartFile.fromBytes(
        'image',
        imageBytes,
        filename: fileName,
        contentType: MediaType(mimeTypeParts[0], mimeTypeParts[1]),
      ),
    );

    // GPS coordinates + form fields
    request.fields['title'] = title;
    request.fields['description'] = description;
    request.fields['latitude'] = latitude;
    request.fields['longitude'] = longitude;
    request.fields['address'] = address ?? 'Unknown Location';
    request.fields['reported_by'] = reportedBy;
    if (reporterEmail != null) request.fields['reporter_email'] = reporterEmail;
    if (voiceTranscript != null) {
      request.fields['voice_transcript'] = voiceTranscript;
    }

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    return jsonDecode(response.body);
  }

  /// Get all issues
  static Future<List<Issue>> getAllIssues() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/issues/all'),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data
          .map((json) => Issue.fromJson(json as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  /// Get issues reported by a specific user
  static Future<List<Issue>> getUserReports(String userId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/user/reports/$userId'),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['success'] == true) {
        final List<dynamic> issues = data['issues'];
        return issues
            .map((json) => Issue.fromJson(json as Map<String, dynamic>))
            .toList();
      }
    }
    return [];
  }

  /// Get issue status by ID
  static Future<Map<String, dynamic>?> getIssueStatus(String issueId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/issues/$issueId/status'),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Error getting issue status: $e');
    }
    return null;
  }

  // ==================== AI (Backend-Processed) ====================

  /// Get AI-generated summary for an issue.
  /// Backend calls inspector_agent.py → Gemini to generate the summary.
  static Future<Map<String, dynamic>> getAISummary(String issueId) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/issues/$issueId/ai-summary'))
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return {'error': 'Failed to get AI summary (${response.statusCode})'};
    } catch (e) {
      return {'error': 'AI Summary unavailable: $e'};
    }
  }

  /// Get predictive hotspots — clusters of issues detected by backend AI.
  /// Backend calls predictive_analytics.py to detect spatial clusters.
  static Future<List<dynamic>> getHotspots() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/analytics/hotspots'))
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as List<dynamic>;
      }
    } catch (e) {
      print('Error getting hotspots: $e');
    }
    return [];
  }

  // ==================== ANALYTICS ====================

  static Future<Map<String, dynamic>> getAnalyticsStats() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/analytics/stats'),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print('Error getting analytics: $e');
    }
    return {'total': 0, 'pending': 0, 'assigned': 0, 'resolved': 0};
  }

  /// Helper: Get full image URL from backend image_path
  static String getImageUrl(String? imagePath) {
    if (imagePath == null || imagePath.isEmpty) return '';
    return '$baseUrl/$imagePath';
  }

  // ==================== CHATBOT (Backend AI) ====================

  /// Send message to AI chatbot.
  /// Backend processes via chatbot_engine.py → Gemini AI.
  /// User prompt is sent as JSON body.
  static Future<Map<String, dynamic>> sendChatMessage({
    required String userId,
    required String message,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/chatbot/message'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'message': message,
        }),
      );
      return jsonDecode(response.body);
    } catch (e) {
      return {'success': false, 'error': 'Connection failed: $e'};
    }
  }

  /// Clear chatbot conversation
  static Future<void> clearChat(String userId) async {
    try {
      await http.post(Uri.parse('$baseUrl/api/chatbot/clear/$userId'));
    } catch (e) {
      print('Clear chat error: $e');
    }
  }
}
