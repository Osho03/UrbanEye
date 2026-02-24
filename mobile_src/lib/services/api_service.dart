/// API Service for UrbanEye - Communicates with Flask Backend
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:mime/mime.dart';
import '../models/issue_model.dart';

class ApiService {
  // For Android emulator: 10.0.2.2 maps to host machine's localhost
  // For physical device: use your computer's local IP address
  static String baseUrl = 'http://10.0.2.2:5000';

  /// Configure base URL (call from settings)
  static void setBaseUrl(String url) {
    baseUrl = url;
  }

  // ==================== HEALTH ====================
  
  static Future<bool> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/health'),
      ).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      print('Health check failed: $e');
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

  /// Report a new issue with image upload
  static Future<Map<String, dynamic>> reportIssue({
    required File imageFile,
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

    // Add image file
    final mimeType = lookupMimeType(imageFile.path) ?? 'image/jpeg';
    final mimeTypeParts = mimeType.split('/');
    request.files.add(
      await http.MultipartFile.fromPath(
        'image',
        imageFile.path,
        contentType: MediaType(mimeTypeParts[0], mimeTypeParts[1]),
      ),
    );

    // Add form fields
    request.fields['title'] = title;
    request.fields['description'] = description;
    request.fields['latitude'] = latitude;
    request.fields['longitude'] = longitude;
    request.fields['address'] = address ?? 'Unknown Location';
    request.fields['reported_by'] = reportedBy;
    if (reporterEmail != null) request.fields['reporter_email'] = reporterEmail;
    if (voiceTranscript != null) request.fields['voice_transcript'] = voiceTranscript;

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
      return data.map((json) => Issue.fromJson(json as Map<String, dynamic>)).toList();
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
        return issues.map((json) => Issue.fromJson(json as Map<String, dynamic>)).toList();
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
    // Backend stores paths like "uploads/filename.jpg"
    return '$baseUrl/$imagePath';
  }
}
