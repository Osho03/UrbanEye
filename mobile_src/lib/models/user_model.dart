/// User model for UrbanEye
class User {
  final String userId;
  final String name;
  final String email;
  final String? phone;
  final String? role;
  final String? token;

  User({
    required this.userId,
    required this.name,
    required this.email,
    this.phone,
    this.role,
    this.token,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      userId: json['user_id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      phone: json['phone'] as String?,
      role: json['role'] as String?,
      token: json['token'] as String?,
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
    };
  }
}
