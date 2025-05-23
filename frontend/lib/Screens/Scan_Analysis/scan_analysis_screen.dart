import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:frontend/constants.dart';
import 'package:frontend/Screens/Scan_Analysis/scan_result_screen.dart';

class ScanAnalysisScreen extends StatefulWidget {
  final String token;

  const ScanAnalysisScreen({
    Key? key,
    required this.token,
  }) : super(key: key);

  @override
  _ScanAnalysisScreenState createState() => _ScanAnalysisScreenState();
}

class _ScanAnalysisScreenState extends State<ScanAnalysisScreen> {
  File? _image;
  final ImagePicker _picker = ImagePicker();
  String _selectedScanType = 'X-ray';
  String _selectedTargetArea = 'Chest';
  bool _isLoading = false;

  final List<String> _scanTypes = ['X-ray', 'MRI', 'CT Scan'];
  final List<String> _targetAreas = [
    'Chest',
    'Brain',
    'Abdomen',
    'Spine',
    'Joints',
    'Other'
  ];

  Future<void> _pickImage() async {
    try {
      final XFile? pickedFile = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 80,
      );

      if (pickedFile != null) {
        setState(() {
          _image = File(pickedFile.path);
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error picking image: $e')),
      );
    }
  }

  Future<void> _analyzeScan() async {
    if (_image == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select an image first')),
      );
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
        Uri.parse('http://192.168.18.60:8000/scan/analyze'),
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
            // Image Preview
            Container(
              height: 300,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: _image != null
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
                            'No image selected',
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

            // Upload Button
            ElevatedButton.icon(
              onPressed: _pickImage,
              icon: const Icon(Icons.upload_file),
              label: const Text('Upload Scan'),
              style: ElevatedButton.styleFrom(
                backgroundColor: kPrimaryColor,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
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
                  : const Text(
                      'Analyze Scan',
                      style: TextStyle(fontSize: 16),
                    ),
            ),
          ],
        ),
      ),
    );
  }
} 