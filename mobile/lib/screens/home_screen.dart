import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/feature_flag_service.dart';
import '../services/api_service.dart';
import '../services/notification_service.dart';
import '../services/fcm_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic> _stats = {};
  Map<String, dynamic> _modelHealth = {};
  bool _benchmarkRunning = false;
  Map<String, dynamic> _userImpact = {'total_impact': 0, 'rank': 'Bronze Citizen'};
  bool _isBackendConnected = false;

  @override
  void initState() {
    super.initState();
    _loadData();
    // Real-time report updates + Firebase push registration once logged in.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final auth = Provider.of<AuthService>(context, listen: false);
      if (auth.currentUser != null) {
        NotificationService.instance.start(userId: auth.currentUser!.userId);
        FcmService.instance.registerToken(auth.currentUser!.userId);
      }
    });
  }

  @override
  void dispose() {
    NotificationService.instance.stop();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final featureFlags = Provider.of<FeatureFlagService>(context, listen: false);
      final results = await Future.wait([
        ApiService.healthCheck(),
        featureFlags.fetchFlags(),
      ]);

      final connected = results[0] as bool;
      Map<String, dynamic> stats = {};
      Map<String, dynamic> modelHealth = {};
      if (connected) {
        final statsAndHealth = await Future.wait([
          ApiService.getAnalyticsStats(),
          ApiService.getModelHealth(),
        ]);
        stats = statsAndHealth[0];
        modelHealth = statsAndHealth[1];
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
          _modelHealth = modelHealth;
          _benchmarkRunning = _readBenchmarkRunning(modelHealth);
          _userImpact = impact;
        });
      }
    } catch (e) {
      // Error loading data, silently handled
    }
  }

  bool _readBenchmarkRunning(Map<String, dynamic> health) {
    final b = health['benchmark'];
    if (b is Map<String, dynamic>) {
      return b['running'] == true;
    }
    return false;
  }

  Future<void> _runBenchmarkNow() async {
    if (_benchmarkRunning) return;
    final started = await ApiService.startBenchmark();
    if (!mounted || !started) return;
    setState(() => _benchmarkRunning = true);

    // Poll the backend until the async benchmark job finishes (~2 min).
    for (int attempt = 0; attempt < 70 && mounted; attempt++) {
      await Future.delayed(const Duration(seconds: 5));
      Map<String, dynamic> health = {'error': 'Network error'};
      try {
        health = await ApiService.getModelHealth();
      } catch (_) {}
      if (!mounted) return;
      final stillRunning = _readBenchmarkRunning(health);
      setState(() {
        _modelHealth = health['error'] == null ? health : _modelHealth;
        _benchmarkRunning = stillRunning;
      });
      if (!stillRunning) break;
    }
    if (mounted && _benchmarkRunning) {
      setState(() => _benchmarkRunning = false);
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
                color: const Color(0xFF4285F4).withValues(alpha: 0.05),
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
                // AI Model Health Card (Self-improving AI)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
                    child: _buildModelHealthCard(),
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

  // ============ AI Model Health Card ============

  Widget _buildModelHealthCard() {
    final bool hasData = _isBackendConnected &&
        _modelHealth.isNotEmpty &&
        _modelHealth['error'] == null &&
        _modelHealth['eval'] != null;

    final Map<String, dynamic> evalModels =
        (hasData && _modelHealth['eval'] is Map<String, dynamic>)
            ? ((_modelHealth['eval'] as Map<String, dynamic>)['models']
                    as Map<String, dynamic>?)
                ?? {}
            : {};

    return _buildGlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF4285F4).withValues(alpha: 0.1),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.monitor_heart_rounded,
                    color: Color(0xFF4285F4), size: 20),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'AI Model Health',
                  style: GoogleFonts.inter(
                    fontWeight: FontWeight.w700,
                    fontSize: 16,
                    color: const Color(0xFF202124),
                  ),
                ),
              ),
              _buildRetrainPill(hasData),
            ],
          ),
          const SizedBox(height: 16),

          if (!hasData)
            Text(
              'Model benchmarks unavailable right now.\nPull down to refresh.',
              style: GoogleFonts.inter(
                fontSize: 12,
                color: const Color(0xFF5F6368),
                height: 1.4,
              ),
            )
          else ...[
            _buildAccuracyBar(
              label: 'Object Detector (YOLOv8)',
              accuracy: _readAccuracy(evalModels, 'yolov8_onnx'),
              color: const Color(0xFFFBBC04),
            ),
            const SizedBox(height: 12),
            _buildAccuracyBar(
              label: 'Image Classifier (MobileNet)',
              accuracy: _readAccuracy(evalModels, 'mobilenetv2'),
              color: const Color(0xFF4285F4),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Icon(Icons.photo_library_outlined,
                    size: 14, color: Color(0xFF5F6368)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Tested on ${_modelHealth['eval']?['n_samples'] ?? '-'} '
                    'real citizen photos (held-out set)',
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      color: const Color(0xFF5F6368),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            _buildRetrainStatusLine(),
            const SizedBox(height: 6),
            if (_benchmarkRunning)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Re-testing every model against ${_modelHealth['eval']?['n_samples'] ?? 'the'} real photos now…',
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          color: const Color(0xFF4285F4),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              )
            else
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Expanded(
                    child: TextButton.icon(
                      onPressed: _runBenchmarkNow,
                      icon: const Icon(Icons.play_circle_outline,
                          size: 16, color: Color(0xFF34A853)),
                      label: Text(
                        'Run benchmark now',
                        style: GoogleFonts.inter(
                            fontSize: 12, fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextButton.icon(
                      onPressed: _showModelHealthCharts,
                      icon: const Icon(Icons.search_rounded, size: 16),
                      label: Text(
                        'Accuracy charts',
                        style: GoogleFonts.inter(
                            fontSize: 12, fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                ],
              ),
          ],
        ],
      ),
    );
  }

  double? _readAccuracy(Map<String, dynamic> evalModels, String key) {
    final m = evalModels[key];
    if (m is Map<String, dynamic> && m['metrics'] is Map<String, dynamic>) {
      final acc = (m['metrics'] as Map<String, dynamic>)['accuracy'];
      if (acc is num) return acc.toDouble();
    }
    return null;
  }

  Widget _buildRetrainPill(bool hasData) {
    final bool on = hasData && (_modelHealth['auto_retrain_enabled'] ?? false) == true;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: on ? Colors.green[50] : Colors.grey[200],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(Icons.autorenew, size: 11,
              color: on ? Colors.green.shade700 : Colors.grey[600]),
          const SizedBox(width: 4),
          Text(
            on ? 'Self-training' : 'Retrain off',
            style: TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.bold,
              color: on ? Colors.green.shade800 : Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAccuracyBar({required String label, double? accuracy, required Color color}) {
    final double frac = accuracy != null ? accuracy.clamp(0.0, 1.0) : 0.0;
    final String txt = accuracy != null
        ? '${(accuracy * 100).toStringAsFixed(1)}%'
        : '--';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF5F6368),
                  fontWeight: FontWeight.w500),
            ),
            Text(
              txt,
              style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w800,
                  color: color),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: Container(
            height: 8,
            color: color.withValues(alpha: 0.12),
            child: Align(
              alignment: Alignment.centerLeft,
              child: FractionallySizedBox(
                widthFactor: accuracy != null ? frac : 0.0,
                child: Container(
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(6),
                    gradient: LinearGradient(
                      colors: [color.withValues(alpha: 0.7), color],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRetrainStatusLine() {
    final dyn = _modelHealth['last_decision'];
    final String dataset = (_modelHealth['dataset_images'] ?? 0).toString();
    String text;
    IconData icon;
    Color color;

    if (dyn is Map<String, dynamic>) {
      final verdict = dyn['verdict']?.toString() ?? '';
      final double? cand = dyn['candidate_acc'] is num
          ? (dyn['candidate_acc'] as num).toDouble()
          : null;
      final double? live = dyn['live_acc'] is num
          ? (dyn['live_acc'] as num).toDouble()
          : null;
      final String c = cand != null ? '${(cand * 100).toStringAsFixed(1)}%' : '--';
      final String l = live != null ? '${(live * 100).toStringAsFixed(1)}%' : '--';
      if (verdict == 'promoted') {
        text = 'Last retrain: model improved to $c and was promoted';
        icon = Icons.check_circle; color = Colors.green;
      } else if (verdict == 'rejected') {
        text = 'Last retrain: weaker model ($c < $l) was safely blocked';
        icon = Icons.shield_rounded; color = Colors.orange;
      } else {
        text = 'Auto-retrain loop checked; no new data yet';
        icon = Icons.info_outline; color = Colors.grey;
      }
    } else {
      text = 'Learning from $dataset verified citizen photos so far';
      icon = Icons.school_outlined; color = const Color(0xFF4285F4);
    }
    return Row(
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            text,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: GoogleFonts.inter(
              fontSize: 11,
              color: const Color(0xFF5F6368),
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }

  void _showModelHealthCharts() {
    final charts = _modelHealth['charts'];
    final List<String> urls = <String>[];
    if (charts is Map<String, dynamic>) {
      final shown = <String>{
        'yolov8_onnx/confusion',
        'yolov8_onnx/performance',
        'mobilenetv2/confusion',
        'mobilenetv2/performance',
      };
      for (final key in shown) {
        final v = charts[key];
        if (v is String && v.isNotEmpty) urls.add(v);
      }
    }

    showDialog<void>(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: const Color(0xFFF8F9FE),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'AI Model Benchmark',
                style: GoogleFonts.inter(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: const Color(0xFF202124),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Every model is evaluated on the same set of real citizen '
                'photos. Yellow = detector, Blue = classifier.',
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(
                  fontSize: 11,
                  color: const Color(0xFF5F6368),
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 12),
              Flexible(
                child: urls.isEmpty
                    ? const Padding(
                        padding: EdgeInsets.all(24),
                        child: Text('No benchmark charts available yet.'),
                      )
                    : ListView.separated(
                        shrinkWrap: true,
                        itemCount: urls.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 12),
                        itemBuilder: (context, i) => ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: InteractiveViewer(
                            maxScale: 4,
                            child: Image.network(
                              urls[i],
                              fit: BoxFit.cover,
                              loadingBuilder: (context, child, progress) =>
                                  progress == null
                                      ? child
                                      : Container(
                                          height: 180,
                                          color: const Color(0xFFE8F0FE),
                                          alignment: Alignment.center,
                                          child: const CircularProgressIndicator(),
                                        ),
                              errorBuilder: (context, error, stack) => Container(
                                height: 120,
                                alignment: Alignment.center,
                                color: const Color(0xFFF1F3F4),
                                child: const Text('Chart unavailable'),
                              ),
                            ),
                          ),
                        ),
                      ),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text('Close',
                    style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ============ Shared building blocks ============

  Widget _buildGlassCard({required Widget child}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.7),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.white.withValues(alpha: 0.5)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.03),
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
              color: color.withValues(alpha: 0.08),
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
                color: color.withValues(alpha: 0.1),
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
            color: Colors.black.withValues(alpha: 0.2),
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
            color: const Color(0xFF202124).withValues(alpha: 0.3),
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
              color: Colors.amber.withValues(alpha: 0.2),
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
                  color: Colors.white.withValues(alpha: 0.1),
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