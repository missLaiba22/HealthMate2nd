import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:frontend/constants.dart';
import 'package:frontend/Screens/Scan_Analysis/scan_result_screen.dart';
import 'package:frontend/Screens/Scan_Analysis/mri_segmentation_results_screen.dart';
import 'package:frontend/Screens/Scan_Analysis/breast_ultrasound_results_screen.dart';
import 'package:frontend/services/segmentation_service.dart';

class ScanAnalysisScreen extends StatefulWidget {
  final String token;
  final String? patientEmail;

  const ScanAnalysisScreen({
    Key? key,
    required this.token,
    this.patientEmail,
  }) : super(key: key);

  @override
  _ScanAnalysisScreenState createState() => _ScanAnalysisScreenState();
}

class _ScanAnalysisScreenState extends State<ScanAnalysisScreen> {
  File? _image;
  File? _secondImage; // For two-modalities (FLAIR + T1CE)
  final ImagePicker _picker = ImagePicker();
  String _selectedScanType = 'X-ray';
  String _selectedTargetArea = 'Chest';
  bool _isLoading = false;

  final List<String> _scanTypes = ['X-ray', 'MRI', 'CT Scan', 'Ultrasound'];
  final List<String> _targetAreas = [
    'Chest',
    'Brain',
    'Abdomen',
    'Spine',
    'Joints',
    'Breast',
    'Other'
  ];

  final _api = SegmentationApiService(baseUrl: ApiConfig.baseUrl);

  Uint8List? _overlayBytes;
  bool _loading = false;

  // Check if two images are required
  bool get _requiresTwoImages => _selectedScanType == 'MRI' && _selectedTargetArea == 'Brain';
  
  // Check if breast ultrasound segmentation is required
  bool get _requiresBreastSegmentation => _selectedScanType == 'Ultrasound' && _selectedTargetArea == 'Breast';

  Future<void> _pickImage() async {
    try {
      final XFile? pickedFile = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 80,
      );

      if (pickedFile != null) {
        setState(() {
          _image = File(pickedFile.path);
          // Clear second image when first image changes
          _secondImage = null;
          _overlayBytes = null;
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error picking image: $e')),
      );
    }
  }

  Future<void> _pickSecondImage() async {
    try {
      final XFile? pickedFile = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 80,
      );

      if (pickedFile != null) {
        setState(() {
          _secondImage = File(pickedFile.path);
          _overlayBytes = null; // Clear previous results
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error picking second image: $e')),
      );
    }
  }

  Future<void> _analyzeScan() async {
    // Check if required images are selected
    if (_image == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select the first image (FLAIR)')),
      );
      return;
    }

    if (_requiresTwoImages && _secondImage == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select the second image (T1CE) for brain MRI segmentation')),
      );
      return;
    }

    // If Ultrasound + Breast, perform breast segmentation
    if (_requiresBreastSegmentation) {
      try {
        setState(() {
          _isLoading = true;
        });

        final imageBytes = await _image!.readAsBytes();
        final imageB64 = base64Encode(imageBytes);

        final response = await http.post(
          Uri.parse('${ApiConfig.baseUrl}/scan/segment/breast'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ${widget.token}',
          },
          body: jsonEncode({
            'image_data': imageB64,
          }),
        );

        if (response.statusCode == 200) {
          final result = jsonDecode(response.body);
          final overlayB64 = result['overlay_png_base64'] as String;
          final overlayBytes = SegmentationApiService.decodeBase64Image(overlayB64);
          
          // Navigate to breast ultrasound results screen
          if (mounted) {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => BreastUltrasoundResultsScreen(
                  token: widget.token,
                  patientEmail: widget.patientEmail ?? 'Unknown Patient',
                  ultrasoundImage: _image!,
                  overlayImage: overlayBytes,
                  segmentationData: result,
                ),
              ),
            );
          }
        } else {
          throw Exception('Failed to segment breast ultrasound: ${response.body}');
        }
        return; // breast segmentation handled
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Breast segmentation error: $e')),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
      return;
    }

    // If MRI + Brain, perform segmentation instead of generic analyze
    if (_requiresTwoImages) {
      try {
        setState(() {
          _isLoading = true;
        });

        final flairBytes = await _image!.readAsBytes();
        final t1ceBytes = await _secondImage!.readAsBytes();
        final flairB64 = base64Encode(flairBytes);
        final t1ceB64 = base64Encode(t1ceBytes);

        final res = await _api.segmentTwoModalities(
          flairBase64: flairB64,
          t1ceBase64: t1ceB64,
        );
        final overlayB64 = res['overlay_png_base64'] as String;
        final overlayBytes = SegmentationApiService.decodeBase64Image(overlayB64);
        
        // Navigate to MRI segmentation results screen
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => MRISegmentationResultsScreen(
                token: widget.token,
                patientEmail: widget.patientEmail ?? 'Unknown Patient',
                flairImage: _image!,
                t1ceImage: _secondImage!,
                overlayImage: overlayBytes,
                segmentationData: res,
              ),
            ),
          );
        }
        return; // segmentation handled
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Segmentation error: $e')),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Convert image to base64
      final bytes = await _image!.readAsBytes();
      final base64Image = base64Encode(bytes);

      // Make API request
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/scan/analyze'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${widget.token}',
        },
        body: jsonEncode({
          'image_data': base64Image,
          'scan_type': _selectedScanType,
          'target_area': _selectedTargetArea,
        }),
      );

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ScanResultScreen(
                analysisResult: result,
                image: _image!,
              ),
            ),
          );
        }
      } else {
        throw Exception('Failed to analyze scan: ${response.body}');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _pickAndSegment() async {
    try {
      setState(() => _loading = true);
      final flair = await _picker.pickImage(source: ImageSource.gallery);
      final t1ce = await _picker.pickImage(source: ImageSource.gallery);
      if (flair == null || t1ce == null) return;

      final flairBytes = await flair.readAsBytes();
      final t1ceBytes = await t1ce.readAsBytes();
      final flairB64 = base64Encode(flairBytes);
      final t1ceB64 = base64Encode(t1ceBytes);

      final res = await _api.segmentTwoModalities(
        flairBase64: flairB64,
        t1ceBase64: t1ceB64,
      );

      final overlayB64 = res['overlay_png_base64'] as String;
      setState(() => _overlayBytes = SegmentationApiService.decodeBase64Image(overlayB64));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Segmentation error: $e')),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Analysis'),
        backgroundColor: kPrimaryColor,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Image/Overlay Preview
            Container(
              height: 300,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: _overlayBytes != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.memory(
                        _overlayBytes!,
                        fit: BoxFit.cover,
                      ),
                    )
                  : _image != null
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.file(
                            _image!,
                            fit: BoxFit.cover,
                          ),
                        )
                      : Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.add_photo_alternate,
                            size: 64,
                            color: Colors.grey[400],
                          ),
                          const SizedBox(height: 16),
                          Text(
                            _requiresTwoImages 
                                ? 'Select FLAIR image first'
                                : _requiresBreastSegmentation
                                    ? 'Select breast ultrasound image'
                                    : 'No image selected',
                            style: TextStyle(
                              color: Colors.grey[600],
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ),
            ),
            const SizedBox(height: 24),

            // Upload Buttons
            ElevatedButton.icon(
              onPressed: _pickImage,
              icon: const Icon(Icons.upload_file),
              label: Text(_requiresTwoImages 
                  ? 'Upload FLAIR Image' 
                  : _requiresBreastSegmentation 
                      ? 'Upload Breast Ultrasound' 
                      : 'Upload Scan'),
              style: ElevatedButton.styleFrom(
                backgroundColor: kPrimaryColor,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            
            // Second image button for two-modalities
            if (_requiresTwoImages) ...[
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _pickSecondImage,
                icon: const Icon(Icons.upload_file),
                label: const Text('Upload T1CE Image'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              
              // Show second image preview if selected
              if (_secondImage != null) ...[
                const SizedBox(height: 16),
                Container(
                  height: 200,
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.file(
                      _secondImage!,
                      fit: BoxFit.cover,
                    ),
                  ),
                ),
              ],
            ],
            const SizedBox(height: 24),

            // Scan Type Dropdown
            DropdownButtonFormField<String>(
              value: _selectedScanType,
              decoration: InputDecoration(
                labelText: 'Scan Type',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              items: _scanTypes.map((String type) {
                return DropdownMenuItem<String>(
                  value: type,
                  child: Text(type),
                );
              }).toList(),
              onChanged: (String? newValue) {
                if (newValue != null) {
                  setState(() {
                    _selectedScanType = newValue;
                    // Clear images when scan type changes
                    _image = null;
                    _secondImage = null;
                    _overlayBytes = null;
                  });
                }
              },
            ),
            const SizedBox(height: 16),

            // Target Area Dropdown
            DropdownButtonFormField<String>(
              value: _selectedTargetArea,
              decoration: InputDecoration(
                labelText: 'Target Area',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              items: _targetAreas.map((String area) {
                return DropdownMenuItem<String>(
                  value: area,
                  child: Text(area),
                );
              }).toList(),
              onChanged: (String? newValue) {
                if (newValue != null) {
                  setState(() {
                    _selectedTargetArea = newValue;
                    // Clear images when target area changes
                    _image = null;
                    _secondImage = null;
                    _overlayBytes = null;
                  });
                }
              },
            ),
            const SizedBox(height: 24),

            // Analyze Button
            ElevatedButton(
              onPressed: _isLoading ? null : _analyzeScan,
              style: ElevatedButton.styleFrom(
                backgroundColor: kPrimaryColor,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: _isLoading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : Text(
                      _requiresTwoImages 
                          ? 'Segment Brain MRI' 
                          : _requiresBreastSegmentation 
                              ? 'Segment Breast Ultrasound' 
                              : 'Analyze Scan',
                      style: const TextStyle(fontSize: 16),
                    ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
} 