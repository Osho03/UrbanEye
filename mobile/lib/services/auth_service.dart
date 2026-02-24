/// Auth Service - Manages user state and local storage
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import 'api_service.dart';

class AuthService extends ChangeNotifier {
  User? _currentUser;
  bool _isLoading = false;

  User? get currentUser => _currentUser;
  bool get isLoggedIn => _currentUser != null;
  bool get isLoading => _isLoading;
  String get userName => _currentUser?.name ?? 'Guest';
  String get userEmail => _currentUser?.email ?? '';
  String get userId => _currentUser?.userId ?? '';

  /// Load user from SharedPreferences on app start
  Future<void> loadUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userData = prefs.getString('user_data');
    if (userData != null) {
      try {
        _currentUser = User.fromJson(jsonDecode(userData));
        notifyListeners();
      } catch (e) {
        print('Error loading user: $e');
        await prefs.remove('user_data');
      }
    }
  }

  /// Register a new user
  Future<String?> register({
    required String name,
    required String email,
    required String password,
    String? phone,
  }) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.register(
        name: name,
        email: email,
        password: password,
        phone: phone,
      );

      if (response['success'] == true) {
        _currentUser = User.fromJson(response['user']);
        await _saveUser();
        _isLoading = false;
        notifyListeners();
        return null; // success
      } else {
        _isLoading = false;
        notifyListeners();
        return response['message'] ?? 'Registration failed';
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return 'Network error: Cannot reach server. Check your connection.';
    }
  }

  /// Login with email and password
  Future<String?> login({
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.login(
        email: email,
        password: password,
      );

      if (response['success'] == true) {
        _currentUser = User.fromJson(response['user']);
        await _saveUser();
        _isLoading = false;
        notifyListeners();
        return null; // success
      } else {
        _isLoading = false;
        notifyListeners();
        return response['message'] ?? 'Login failed';
      }
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return 'Network error: Cannot reach server. Check your connection.';
    }
  }

  /// Logout
  Future<void> logout() async {
    _currentUser = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('user_data');
    notifyListeners();
  }

  /// Save user to SharedPreferences
  Future<void> _saveUser() async {
    if (_currentUser != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('user_data', jsonEncode(_currentUser!.toJson()));
    }
  }

  /// Update user info locally after profile edit
  Future<void> updateLocalUser({String? name, String? phone}) async {
    if (_currentUser != null) {
      _currentUser = User(
        userId: _currentUser!.userId,
        name: name ?? _currentUser!.name,
        email: _currentUser!.email,
        phone: phone ?? _currentUser!.phone,
        role: _currentUser!.role,
        token: _currentUser!.token,
      );
      await _saveUser();
      notifyListeners();
    }
  }
}
