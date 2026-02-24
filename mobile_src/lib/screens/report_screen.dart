/// Report Screen - Camera + GPS + Voice + Submit
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:provider/provider.dart';
import 'package:path/path.dart' as path;
import '../services/auth_service.dart';
import '../services/api_service.dart';

class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();

  File? _imageFile;
  String? _latitude;
  String? _longitude;
  String? _address;
  bool _isSubmitting = false;
  bool _isCapturingLocation = false;
  bool _isListening = false;
  String? _compressionInfo;

  final ImagePicker _picker = ImagePicker();
  final stt.SpeechToText _speech = stt.SpeechToText();

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  /// Capture image from camera
  Future<void> _captureImage() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 85,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (photo != null) {
        // Compress image
        final compressed = await _compressImage(File(photo.path));
        setState(() {
          _imageFile = compressed;
        });
        // Auto-capture GPS after taking photo
        _captureLocation();
      }
    } catch (e) {
      _showError('Camera error: $e');
    }
  }

  /// Pick from gallery
  Future<void> _pickFromGallery() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );

      if (photo != null) {
        final compressed = await _compressImage(File(photo.path));
        setState(() {
          _imageFile = compressed;
        });
        _captureLocation();
      }
    } catch (e) {
      _showError('Gallery error: $e');
    }
  }

  /// Compress image before upload
  Future<File> _compressImage(File file) async {
    final originalSize = await file.length();
    
    try {
      final dir = path.dirname(file.path);
      final targetPath = path.join(dir, 'compressed_${path.basename(file.path)}');

      final result = await FlutterImageCompress.compressAndGetFile(
        file.absolute.path,
        targetPath,
        quality: 70,
        minWidth: 1024,
        minHeight: 1024,
      );

      if (result != null) {
        final compressedFile = File(result.path);
        final compressedSize = await compressedFile.length();
        final savings = ((1 - compressedSize / originalSize) * 100).toStringAsFixed(0);
        
        setState(() {
          _compressionInfo = 'Compressed: ${(compressedSize / 1024).toStringAsFixed(0)}KB (saved $savings%)';
        });
        
        return compressedFile;
      }
    } catch (e) {
      print('Compression failed, using original: $e');
    }

    setState(() {
      _compressionInfo = 'Original: ${(originalSize / 1024).toStringAsFixed(0)}KB';
    });
    return file;
  }

  /// Capture GPS location
  Future<void> _captureLocation() async {
    setState(() => _isCapturingLocation = true);

    try {
      // Check permission
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          _showError('Location permission denied');
          setState(() => _isCapturingLocation = false);
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        _showError('Location permissions permanently denied. Please enable in settings.');
        setState(() => _isCapturingLocation = false);
        return;
      }

      // Get position
      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      // Reverse geocode
      String address = 'Unknown Location';
      try {
        final placemarks = await placemarkFromCoordinates(
          position.latitude,
          position.longitude,
        );
        if (placemarks.isNotEmpty) {
          final p = placemarks.first;
          address = [p.street, p.subLocality, p.locality, p.administrativeArea]
              .where((s) => s != null && s.isNotEmpty)
              .join(', ');
        }
      } catch (e) {
        print('Geocoding failed: $e');
      }

      setState(() {
        _latitude = position.latitude.toStringAsFixed(6);
        _longitude = position.longitude.toStringAsFixed(6);
        _address = address;
        _isCapturingLocation = false;
      });
    } catch (e) {
      _showError('Location error: $e');
      setState(() => _isCapturingLocation = false);
    }
  }

  /// Voice input
  Future<void> _toggleVoiceInput() async {
    if (_isListening) {
      _speech.stop();
      setState(() => _isListening = false);
      return;
    }

    final available = await _speech.initialize(
      onStatus: (status) {
        if (status == 'done' || status == 'notListening') {
          setState(() => _isListening = false);
        }
      },
      onError: (error) {
        _showError('Speech error: ${error.errorMsg}');
        setState(() => _isListening = false);
      },
    );

    if (available) {
      setState(() => _isListening = true);
      _speech.listen(
        onResult: (result) {
          setState(() {
            _descriptionController.text = result.recognizedWords;
          });
        },
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 5),
      );
    } else {
      _showError('Speech recognition not available');
    }
  }

  /// Submit report
  Future<void> _submitReport() async {
    if (!_formKey.currentState!.validate()) return;
    if (_imageFile == null) {
      _showError('Please capture or select an image');
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final auth = Provider.of<AuthService>(context, listen: false);

      final result = await ApiService.reportIssue(
        imageFile: _imageFile!,
        title: _titleController.text.trim(),
        description: _descriptionController.text.trim(),
        latitude: _latitude ?? '0',
        longitude: _longitude ?? '0',
        address: _address,
        reportedBy: auth.userName,
        reporterEmail: auth.userEmail,
      );

      if (!mounted) return;

      setState(() => _isSubmitting = false);

      if (result['message'] != null) {
        // Success
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (ctx) => AlertDialog(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.check_circle, color: Color(0xFF66BB6A), size: 72),
                const SizedBox(height: 16),
                Text(
                  'Issue Reported!',
                  style: GoogleFonts.inter(fontSize: 22, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 8),
                Text(
                  'AI detected: ${result['issue_type'] ?? 'Processing'}',
                  style: GoogleFonts.inter(fontSize: 14, color: Colors.grey.shade600),
                  textAlign: TextAlign.center,
                ),
                if (result['issue_id'] != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    'ID: ${result['issue_id']}',
                    style: GoogleFonts.inter(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ],
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  Navigator.pop(context);
                },
                child: const Text('Done'),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(ctx);
                  _resetForm();
                },
                child: const Text('Report Another'),
              ),
            ],
          ),
        );
      } else {
        _showError(result['error'] ?? 'Failed to submit report');
      }
    } catch (e) {
      setState(() => _isSubmitting = false);
      _showError('Network error: $e');
    }
  }

  void _resetForm() {
    _formKey.currentState?.reset();
    _titleController.clear();
    _descriptionController.clear();
    setState(() {
      _imageFile = null;
      _latitude = null;
      _longitude = null;
      _address = null;
      _compressionInfo = null;
    });
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: Colors.red.shade700,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Issue'),
        actions: [
          if (_imageFile != null || _titleController.text.isNotEmpty)
            IconButton(
              onPressed: _resetForm,
              icon: const Icon(Icons.refresh),
              tooltip: 'Clear Form',
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Image Capture
              GestureDetector(
                onTap: _captureImage,
                child: Container(
                  height: 220,
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: _imageFile != null ? const Color(0xFF66BB6A) : Colors.grey.shade300,
                      width: 2,
                    ),
                    image: _imageFile != null
                        ? DecorationImage(
                            image: FileImage(_imageFile!),
                            fit: BoxFit.cover,
                          )
                        : null,
                  ),
                  child: _imageFile == null
                      ? Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.camera_alt_rounded, size: 56, color: Colors.grey.shade400),
                            const SizedBox(height: 8),
                            Text(
                              'Tap to capture photo',
                              style: GoogleFonts.inter(color: Colors.grey.shade500, fontSize: 16),
                            ),
                            const SizedBox(height: 16),
                            OutlinedButton.icon(
                              onPressed: _pickFromGallery,
                              icon: const Icon(Icons.photo_library_outlined, size: 18),
                              label: const Text('Choose from Gallery'),
                            ),
                          ],
                        )
                      : Align(
                          alignment: Alignment.bottomRight,
                          child: Padding(
                            padding: const EdgeInsets.all(8),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                _MiniButton(
                                  icon: Icons.camera_alt,
                                  onTap: _captureImage,
                                ),
                                const SizedBox(width: 8),
                                _MiniButton(
                                  icon: Icons.photo_library,
                                  onTap: _pickFromGallery,
                                ),
                              ],
                            ),
                          ),
                        ),
                ),
              ),

              // Compression info
              if (_compressionInfo != null) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(Icons.compress, size: 14, color: Colors.green),
                    const SizedBox(width: 4),
                    Text(_compressionInfo!, style: GoogleFonts.inter(fontSize: 12, color: Colors.green.shade700)),
                  ],
                ),
              ],

              const SizedBox(height: 20),

              // GPS Location
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.shade100),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.location_on, color: Colors.blue.shade700, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          'Location',
                          style: GoogleFonts.inter(fontWeight: FontWeight.w600, color: Colors.blue.shade700),
                        ),
                        const Spacer(),
                        if (_isCapturingLocation)
                          const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        else
                          TextButton.icon(
                            onPressed: _captureLocation,
                            icon: const Icon(Icons.my_location, size: 16),
                            label: const Text('Capture GPS'),
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(horizontal: 8),
                              visualDensity: VisualDensity.compact,
                            ),
                          ),
                      ],
                    ),
                    if (_latitude != null && _longitude != null) ...[
                      const SizedBox(height: 8),
                      Text('📍 $_latitude, $_longitude', style: GoogleFonts.inter(fontSize: 13)),
                      if (_address != null)
                        Text('📮 $_address', style: GoogleFonts.inter(fontSize: 13, color: Colors.grey.shade700)),
                    ] else
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          'GPS will auto-capture when you take a photo',
                          style: GoogleFonts.inter(fontSize: 12, color: Colors.grey),
                        ),
                      ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Title
              TextFormField(
                controller: _titleController,
                decoration: const InputDecoration(
                  labelText: 'Issue Title',
                  hintText: 'e.g., Pothole on Main Road',
                  prefixIcon: Icon(Icons.title),
                ),
                validator: (v) => v == null || v.trim().isEmpty ? 'Title required' : null,
              ),

              const SizedBox(height: 16),

              // Description with Voice
              TextFormField(
                controller: _descriptionController,
                maxLines: 4,
                decoration: InputDecoration(
                  labelText: 'Description',
                  hintText: 'Describe the issue...',
                  prefixIcon: const Padding(
                    padding: EdgeInsets.only(bottom: 64),
                    child: Icon(Icons.description_outlined),
                  ),
                  suffixIcon: Padding(
                    padding: const EdgeInsets.only(bottom: 64),
                    child: IconButton(
                      onPressed: _toggleVoiceInput,
                      icon: Icon(
                        _isListening ? Icons.mic : Icons.mic_none,
                        color: _isListening ? Colors.red : null,
                      ),
                      tooltip: 'Voice Input',
                    ),
                  ),
                ),
                validator: (v) => v == null || v.trim().isEmpty ? 'Description required' : null,
              ),

              if (_isListening) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.graphic_eq, color: Colors.red, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'Listening... Speak now',
                        style: GoogleFonts.inter(color: Colors.red.shade700, fontSize: 13),
                      ),
                      const Spacer(),
                      TextButton(
                        onPressed: _toggleVoiceInput,
                        child: const Text('Stop'),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 32),

              // Submit
              ElevatedButton.icon(
                onPressed: _isSubmitting ? null : _submitReport,
                icon: _isSubmitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.send_rounded),
                label: Text(_isSubmitting ? 'Submitting...' : 'Submit Report'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  textStyle: GoogleFonts.inter(fontSize: 17, fontWeight: FontWeight.w600),
                ),
              ),

              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class _MiniButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _MiniButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.black54,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: Colors.white, size: 20),
      ),
    );
  }
}
