/// Map Screen - Shows all reported issues on OpenStreetMap
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../services/api_service.dart';
import '../models/issue_model.dart';
import 'issue_detail_screen.dart';

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  List<Issue> _issues = [];
  bool _isLoading = true;
  final MapController _mapController = MapController();

  @override
  void initState() {
    super.initState();
    _loadIssues();
  }

  Future<void> _loadIssues() async {
    setState(() => _isLoading = true);
    try {
      final issues = await ApiService.getAllIssues();
      if (mounted) {
        setState(() {
          _issues = issues.where((i) =>
            i.latitude != null && i.longitude != null &&
            i.latitude != '0' && i.longitude != '0'
          ).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Issue Map'),
        actions: [
          IconButton(
            onPressed: _loadIssues,
            icon: const Icon(Icons.refresh),
          ),
          IconButton(
            onPressed: () {
              // Reset map to India center
              _mapController.move(LatLng(20.5937, 78.9629), 5);
            },
            icon: const Icon(Icons.zoom_out_map),
            tooltip: 'Reset View',
          ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(20.5937, 78.9629), // India center
              initialZoom: 5,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.urbaneye.mobile',
              ),
              MarkerLayer(
                markers: _issues.map((issue) {
                  double lat = 0, lon = 0;
                  try {
                    lat = double.parse(issue.latitude!);
                    lon = double.parse(issue.longitude!);
                  } catch (_) {
                    return null;
                  }
                  
                  return Marker(
                    point: LatLng(lat, lon),
                    width: 40,
                    height: 40,
                    child: GestureDetector(
                      onTap: () => _showIssuePopup(context, issue),
                      child: Container(
                        decoration: BoxDecoration(
                          color: issue.statusColor,
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 2),
                          boxShadow: [
                            BoxShadow(
                              color: issue.statusColor.withOpacity(0.4),
                              blurRadius: 6,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Icon(
                          _getIssueIcon(issue.issueType),
                          color: Colors.white,
                          size: 18,
                        ),
                      ),
                    ),
                  );
                }).whereType<Marker>().toList(),
              ),
            ],
          ),

          // Legend
          Positioned(
            bottom: 16,
            left: 16,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 8),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('Legend', style: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 12)),
                  const SizedBox(height: 6),
                  _LegendItem(color: const Color(0xFFFFA726), label: 'Pending'),
                  _LegendItem(color: const Color(0xFF42A5F5), label: 'Assigned'),
                  _LegendItem(color: const Color(0xFF66BB6A), label: 'Resolved'),
                ],
              ),
            ),
          ),

          // Issue count badge
          Positioned(
            top: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 8),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.pin_drop, size: 16, color: Color(0xFF1565C0)),
                  const SizedBox(width: 4),
                  Text(
                    '${_issues.length} Issues',
                    style: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ],
              ),
            ),
          ),

          if (_isLoading)
            const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }

  void _showIssuePopup(BuildContext context, Issue issue) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Handle
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Text(
                    issue.title ?? 'Untitled',
                    style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: issue.statusColor,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    issue.status ?? '',
                    style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.category, size: 16, color: Colors.grey.shade500),
                const SizedBox(width: 4),
                Text(issue.displayIssueType, style: GoogleFonts.inter(color: Colors.grey.shade600)),
                const SizedBox(width: 16),
                Icon(Icons.business, size: 16, color: Colors.grey.shade500),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    issue.assignedDepartment ?? 'Unassigned',
                    style: GoogleFonts.inter(color: Colors.grey.shade600),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            if (issue.address != null) ...[
              const SizedBox(height: 6),
              Row(
                children: [
                  Icon(Icons.location_on, size: 16, color: Colors.grey.shade500),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      issue.address!,
                      style: GoogleFonts.inter(fontSize: 13, color: Colors.grey.shade600),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => IssueDetailScreen(issue: issue)),
                  );
                },
                child: const Text('View Details'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  IconData _getIssueIcon(String? issueType) {
    switch (issueType?.toLowerCase()) {
      case 'pothole':
        return Icons.warning_amber;
      case 'garbage':
        return Icons.delete_outline;
      case 'water_leak':
      case 'water leak':
        return Icons.water_drop;
      case 'streetlight':
        return Icons.light;
      default:
        return Icons.report_problem_outlined;
    }
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _LegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(label, style: GoogleFonts.inter(fontSize: 11)),
        ],
      ),
    );
  }
}
