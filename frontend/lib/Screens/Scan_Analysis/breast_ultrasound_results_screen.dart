import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/Screens/Scan_Analysis/scan_analysis_screen.dart';

class BreastUltrasoundResultsScreen extends StatefulWidget {
  final String token;
  final String patientEmail;
  final File ultrasoundImage;
  final Uint8List overlayImage;
  final Map<String, dynamic> segmentationData;

  const BreastUltrasoundResultsScreen({
    Key? key,
    required this.token,
    required this.patientEmail,
    required this.ultrasoundImage,
    required this.overlayImage,
    required this.segmentationData,
  }) : super(key: key);

  @override
  _BreastUltrasoundResultsScreenState createState() => _BreastUltrasoundResultsScreenState();
}

class _BreastUltrasoundResultsScreenState extends State<BreastUltrasoundResultsScreen> {
  bool _isGeneratingReport = false;
  Map<String, dynamic>? _medicalReport;

  @override
  void initState() {
    super.initState();
    _generateMedicalReport();
  }

  Future<void> _generateMedicalReport() async {
    setState(() {
      _isGeneratingReport = true;
    });

    try {
      // Simulate AI-generated medical report based on segmentation
      await Future.delayed(const Duration(seconds: 2));
      
      // Extract measurements and generate insights
      final measurements = widget.segmentationData['measurements'] as Map<String, dynamic>? ?? {};
      final insights = widget.segmentationData['insights'] as List<dynamic>? ?? [];
      final recommendations = widget.segmentationData['recommendations'] as List<dynamic>? ?? [];
      
      setState(() {
        _medicalReport = {
          'patient_email': widget.patientEmail,
          'scan_date': DateTime.now().toIso8601String(),
          'scan_type': 'Breast Ultrasound',
          'measurements': measurements,
          'insights': insights,
          'recommendations': recommendations,
        };
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error generating report: $e')),
      );
    } finally {
      setState(() {
        _isGeneratingReport = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Breast Ultrasound Report'),
        backgroundColor: kPrimaryColor,
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: _shareReport,
          ),
          IconButton(
            icon: const Icon(Icons.print),
            onPressed: _printReport,
          ),
        ],
      ),
      body: _isGeneratingReport
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Generating Medical Report...'),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildPatientInfo(),
                  const SizedBox(height: 24),
                  _buildImageAnalysis(),
                  const SizedBox(height: 24),
                  _buildMeasurements(),
                  const SizedBox(height: 24),
                  _buildMedicalInsights(),
                  const SizedBox(height: 24),
                  _buildRecommendations(),
                  const SizedBox(height: 24),
                  _buildActionButtons(),
                ],
              ),
            ),
    );
  }

  Widget _buildPatientInfo() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.person, color: kPrimaryColor),
                const SizedBox(width: 8),
                Text(
                  'Patient Information',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: kPrimaryColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildInfoRow('Patient ID', widget.patientEmail),
            _buildInfoRow('Scan Date', _formatDate(_medicalReport?['scan_date'])),
            _buildInfoRow('Scan Type', _medicalReport?['scan_type'] ?? 'Breast Ultrasound'),
            _buildInfoRow('Report Status', 'Completed'),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String? value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(value ?? 'N/A'),
          ),
        ],
      ),
    );
  }

  Widget _buildImageAnalysis() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.image, color: kPrimaryColor),
                const SizedBox(width: 8),
                Text(
                  'Image Analysis',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: kPrimaryColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Text('Original Ultrasound Image', style: TextStyle(fontWeight: FontWeight.w500)),
            const SizedBox(height: 8),
            Container(
              height: 200,
              width: double.infinity,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.file(
                  widget.ultrasoundImage,
                  fit: BoxFit.cover,
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text('Segmentation Overlay', style: TextStyle(fontWeight: FontWeight.w500)),
            const SizedBox(height: 8),
            Container(
              height: 200,
              width: double.infinity,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.memory(
                  widget.overlayImage,
                  fit: BoxFit.cover,
                ),
              ),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Container(
                    width: 16,
                    height: 16,
                    decoration: const BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text('Lesion (if detected)'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMeasurements() {
    final measurements = _medicalReport?['measurements'] as Map<String, dynamic>? ?? {};
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.analytics, color: kPrimaryColor),
                const SizedBox(width: 8),
                Text(
                  'Measurements',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: kPrimaryColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildMeasurementRow('Total Image Area', '${measurements['total_image_area']?.toStringAsFixed(2)} cm²', Colors.blue),
            _buildMeasurementRow('Lesion Area', '${measurements['lesion_area']?.toStringAsFixed(2)} cm²', Colors.red),
            _buildMeasurementRow('Lesion Percentage', '${measurements['lesion_percentage']?.toStringAsFixed(2)}%', Colors.orange),
            _buildMeasurementRow('Lesion Present', measurements['lesion_present'] == true ? 'Yes' : 'No', 
                measurements['lesion_present'] == true ? Colors.red : Colors.green),
            _buildMeasurementRow('Image Resolution', '${measurements['total_pixel_count']} pixels', Colors.grey),
          ],
        ),
      ),
    );
  }

  Widget _buildMeasurementRow(String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMedicalInsights() {
    final insights = _medicalReport?['insights'] as List<dynamic>? ?? [];
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.insights, color: kPrimaryColor),
                const SizedBox(width: 8),
                Text(
                  'Medical Insights',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: kPrimaryColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...insights.map((insight) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.check_circle, color: Colors.green, size: 16),
                  const SizedBox(width: 8),
                  Expanded(child: Text(insight.toString())),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendations() {
    final recommendations = _medicalReport?['recommendations'] as List<dynamic>? ?? [];
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.recommend, color: kPrimaryColor),
                const SizedBox(width: 8),
                Text(
                  'Recommendations',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: kPrimaryColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...recommendations.map((recommendation) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 4.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.arrow_forward, color: Colors.blue, size: 16),
                  const SizedBox(width: 8),
                  Expanded(child: Text(recommendation.toString())),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => ScanAnalysisScreen(
                    token: widget.token,
                    patientEmail: widget.patientEmail,
                  ),
                ),
              );
            },
            icon: const Icon(Icons.arrow_back),
            label: const Text('New Analysis'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.grey,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: _saveReport,
            icon: const Icon(Icons.save),
            label: const Text('Save Report'),
            style: ElevatedButton.styleFrom(
              backgroundColor: kPrimaryColor,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
      ],
    );
  }

  String _formatDate(String? dateString) {
    if (dateString == null) return 'N/A';
    try {
      final date = DateTime.parse(dateString);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return 'N/A';
    }
  }

  void _shareReport() {
    // Implement sharing functionality
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Report sharing feature coming soon')),
    );
  }

  void _printReport() {
    // Implement printing functionality
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Print feature coming soon')),
    );
  }

  void _saveReport() {
    // Implement saving functionality
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Report saved successfully')),
    );
  }
}
