/// User model for UrbanEye
class User {
  final String userId;
  final String name;
  final String email;
  final String? phone;
  final String? role;
  final String? token;
  final String? profilePhoto;
  final int? age;
  final String? gender;
  final bool notificationsEnabled;
  final bool notifyStatusUpdates;
  final bool notifyDigest;

  User({
    required this.userId,
    required this.name,
    required this.email,
    this.phone,
    this.role,
    this.token,
    this.profilePhoto,
    this.age,
    this.gender,
    this.notificationsEnabled = true,
    this.notifyStatusUpdates = true,
    this.notifyDigest = false,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      userId: json['user_id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      phone: json['phone'] as String?,
      role: json['role'] as String?,
      token: json['token'] as String?,
      profilePhoto: json['profile_photo'] as String?,
      age: json['age'] is num ? (json['age'] as num).toInt() : json['age'] as int?,
      gender: json['gender'] as String?,
      notificationsEnabled: json['notifications_enabled'] ?? true,
      notifyStatusUpdates: json['notify_status_updates'] ?? true,
      notifyDigest: json['notify_digest'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'name': name,
      'email': email,
      'phone': phone,
      'role': role,
      'token': token,
      'profile_photo': profilePhoto,
      'age': age,
      'gender': gender,
      'notifications_enabled': notificationsEnabled,
      'notify_status_updates': notifyStatusUpdates,
      'notify_digest': notifyDigest,
    };
  }
}