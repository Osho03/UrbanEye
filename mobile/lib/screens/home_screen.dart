import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/feature_flag_service.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  Map<String, dynamic> _stats = {};
  Map<String, dynamic> _userImpact = {'total_impact': 0, 'rank': 'Bronze Citizen'};
  bool _isBackendConnected = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final featureFlags = Provider.of<FeatureFlagService>(context, listen: false);
      final results = await Future.wait([
        ApiService.healthCheck(),
        featureFlags.fetchFlags(),
      ]);

      final connected = results[0] as bool;
      Map<String, dynamic> stats = {};
      if (connected) {
        stats = await ApiService.getAnalyticsStats();
      }

      if (mounted) {
        final auth = Provider.of<AuthService>(context, listen: false);
        Map<String, dynamic> impact = {'total_impact': 0, 'rank': 'Bronze Citizen'};
        if (connected && auth.currentUser != null) {
          impact = await ApiService.getUserImpact(auth.currentUser!.userId);
        }

        setState(() {
          _isBackendConnected = connected;
          _stats = stats;
          _userImpact = impact;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FE),
      body: Stack(
        children: [
          // Background Gradient Blobs
          Positioned(
            top: -50,
            left: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF4285F4).withOpacity(0.05),
              ),
            ),
          ),
          
          RefreshIndicator(
            onRefresh: _loadData,
            child: CustomScrollView(
              physics: const BouncingScrollPhysics(),
              slivers: [
                // Premium Header
                SliverToBoxAdapter(
                  child: Container(
                    padding: const EdgeInsets.fromLTRB(24, 64, 24, 24),
                    child: Row(
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Welcome back,',
                              style: GoogleFonts.inter(
                                fontSize: 14,
                                color: const Color(0xFF5F6368),
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            Text(
                              auth.userName,
                              style: GoogleFonts.inter(
                                fontSize: 24,
                                fontWeight: FontWeight.w800,
                                color: const Color(0xFF202124),
                              ),
                            ),
                          ],
                        ),
                        const Spacer(),
                        GestureDetector(
                          onTap: () => Navigator.pushNamed(context, '/profile'),
                          child: Hero(
                            tag: 'profile_photo',
                            child: Container(
                              padding: const EdgeInsets.all(2),
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(color: const Color(0xFF4285F4), width: 2),
                              ),
                              child: CircleAvatar(
                                radius: 24,
                                backgroundColor: const Color(0xFFE8F0FE),
                                backgroundImage: auth.currentUser?.profilePhoto != null 
                                  ? NetworkImage(auth.currentUser!.profilePhoto!.startsWith('http') 
                                      ? auth.currentUser!.profilePhoto! 
                                      : ApiService.getImageUrl(auth.currentUser!.profilePhoto))
                                  : null,
                                child: auth.currentUser?.profilePhoto == null 
                                  ? const Icon(Icons.person, color: Color(0xFF4285F4))
                                  : null,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // Glassmorphism Stats Section
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildGlassCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text(
                                    'City Health Metrics',
                                    style: GoogleFonts.inter(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 16,
                                      color: const Color(0xFF202124),
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: _isBackendConnected ? Colors.green[50] : Colors.red[50],
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(Icons.circle, size: 8, color: _isBackendConnected ? Colors.green : Colors.red),
                                        const SizedBox(width: 4),
                                        Text(
                                          _isBackendConnected ? 'Online' : 'Offline',
                                          style: TextStyle(
                                            fontSize: 10,
                                            fontWeight: FontWeight.bold,
                                            color: _isBackendConnected ? Colors.green : Colors.red,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 20),
                              Row(
                                children: [
                                  _buildStatItem('Total', _stats['total']?.toString() ?? '0', const Color(0xFF4285F4)),
                                  _buildVerticalDivider(),
                                  _buildStatItem('Pending', _stats['pending']?.toString() ?? '0', const Color(0xFFFBBC04)),
                                  _buildVerticalDivider(),
                                  _buildStatItem('Resolved', _stats['resolved']?.toString() ?? '0', const Color(0xFF34A853)),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // User Impact Card (New Enhancement)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
                    child: _buildImpactCard(),
                  ),
                ),
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(24, 32, 24, 16),
                    child: Text(
                      'Citizen Services',
                      style: GoogleFonts.inter(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: const Color(0xFF202124),
                      ),
                    ),
                  ),
                ),

                // Grid Actions
                SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  sliver: SliverGrid.count(
                    crossAxisCount: 2,
                    mainAxisSpacing: 16,
                    crossAxisSpacing: 16,
                    children: [
                      _buildActionTile(
                        icon: Icons.add_a_photo_rounded,
                        title: 'Report Issue',
                        color: const Color(0xFF4285F4),
                        onTap: () => Navigator.pushNamed(context, '/report'),
                      ),
                      _buildActionTile(
                        icon: Icons.history_rounded,
                        title: 'My Reports',
                        color: const Color(0xFF34A853),
                        onTap: () => Navigator.pushNamed(context, '/my-reports'),
                      ),
                      _buildActionTile(
                        icon: Icons.map_rounded,
                        title: 'City Map',
                        color: const Color(0xFFEA4335),
                        onTap: () => Navigator.pushNamed(context, '/map'),
                      ),
                      _buildActionTile(
                        icon: Icons.auto_awesome_rounded,
                        title: 'AI Insights',
                        color: const Color(0xFFFBBC04),
                        onTap: () => Navigator.pushNamed(context, '/chatbot'),
                      ),
                    ],
                  ),
                ),

                const SliverToBoxAdapter(child: SizedBox(height: 100)),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.pushNamed(context, '/chatbot'),
        backgroundColor: const Color(0xFF202124),
        icon: const Icon(Icons.bolt_rounded, color: Colors.amber),
        label: Text('Ask AI', style: GoogleFonts.inter(fontWeight: FontWeight.bold, color: Colors.white)),
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildGlassCard({required Widget child}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.7),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.white.withOpacity(0.5)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: child,
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, Color color) {
    return Expanded(
      child: Column(
        children: [
          Text(
            value,
            style: GoogleFonts.inter(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: GoogleFonts.inter(
              fontSize: 12,
              color: const Color(0xFF5F6368),
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVerticalDivider() {
    return Container(
      height: 30,
      width: 1,
      color: Colors.grey[300],
    );
  }

  Widget _buildActionTile({required IconData icon, required String title, required Color color, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.08),
              blurRadius: 15,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(height: 12),
            Text(
              title,
              style: GoogleFonts.inter(
                fontSize: 14,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF202124),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      margin: const EdgeInsets.fromLTRB(24, 0, 24, 24),
      height: 70,
      decoration: BoxDecoration(
        color: const Color(0xFF202124),
        borderRadius: BorderRadius.circular(35),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _navItem(Icons.grid_view_rounded, 0, true),
          _navItem(Icons.add_location_alt_rounded, 1, false),
          _navItem(Icons.view_headline_rounded, 2, false),
          _navItem(Icons.map_rounded, 3, false),
        ],
      ),
    );
  }

  Widget _navItem(IconData icon, int index, bool selected) {
    return IconButton(
      icon: Icon(icon, color: selected ? Colors.white : Colors.white54, size: 28),
      onPressed: () {
        switch (index) {
          case 0: break;
          case 1: Navigator.pushNamed(context, '/report'); break;
          case 2: Navigator.pushNamed(context, '/my-reports'); break;
          case 3: Navigator.pushNamed(context, '/map'); break;
        }
      },
    );
  }

  Widget _buildImpactCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF202124), Color(0xFF3C4043)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF202124).withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.amber.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.stars_rounded, color: Colors.amber, size: 32),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Community Impact',
                  style: GoogleFonts.inter(
                    color: Colors.white70,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${_userImpact['total_impact']} Points',
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                'Current Rank',
                style: GoogleFonts.inter(
                  color: Colors.white70,
                  fontSize: 10,
                ),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  _userImpact['rank'] ?? 'Citizen',
                  style: GoogleFonts.inter(
                    color: Colors.amber,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
