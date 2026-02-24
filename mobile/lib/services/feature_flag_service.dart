import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'api_service.dart';

class FeatureFlagService extends ChangeNotifier {
  Map<String, dynamic> _flags = {
    "forensic_ai_enabled": false,
    "cost_prediction_enabled": false,
    "impact_radius_enabled": true,
    "contractor_ai_enabled": false,
  };

  bool _isLoading = true;

  Map<String, dynamic> get flags => _flags;
  bool get isLoading => _isLoading;

  bool isEnabled(String flagName) => _flags[flagName] ?? false;

  Future<void> fetchFlags() async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await http
          .get(
            Uri.parse('${ApiService.baseUrl}/api/features/status'),
          )
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        _flags = jsonDecode(response.body);
        debugPrint('✅ Feature Flags Loaded: $_flags');
      }
    } catch (e) {
      debugPrint('❌ Error fetching feature flags: $e');
      // Keep defaults on error
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
