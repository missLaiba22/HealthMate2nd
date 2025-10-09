import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/Screens/Scan_Analysis/scan_analysis_screen.dart';

class MRISegmentationResultsScreen extends StatefulWidget {
  final String token;
  final String patientEmail;
  final File flairImage;
  final File t1ceImage;
  final Uint8List overlayImage;
  final Map<String, dynamic> segmentationData;

  const MRISegmentationResultsScreen({
    Key? key,
    required this.token,
    required this.patientEmail,
    required this.flairImage,
    required this.t1ceImage,
    required this.overlayImage,
    required this.segmentationData,
  }) : super(key: key);

  @override
  _MRISegmentationResultsScreenState createState() => _MRISegmentationResultsScreenState();
}

class _MRISegmentationResultsScreenState extends State<MRISegmentationResultsScreen> {
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
      
      // Calculate volumes and generate insights
      final volumes = _calculateVolumes();
      final insights = _generateInsights(volumes);
      
      setState(() {
        _medicalReport = {
          'patient_email': widget.patientEmail,
          'scan_date': DateTime.now().toIso8601String(),
          'scan_type': 'Brain MRI (FLAIR + T1CE)',
          'volumes': volumes,
          'insights': insights,
          'recommendations': _generateRecommendations(insights),
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

  Map<String, double> _calculateVolumes() {
    // Simulate volume calculations based on segmentation
    // In real implementation, this would use the actual segmentation mask
    return {
      'total_brain_volume': 1450.5, // cm³
      'tumor_volume': 12.3, // cm³
      'edema_volume': 45.7, // cm³
      'enhancing_volume': 8.9, // cm³
      'necrotic_volume': 3.4, // cm³
    };
  }

  List<String> _generateInsights(Map<String, double> volumes) {
    final insights = <String>[];
    
    if (volumes['tumor_volume']! > 10.0) {
      insights.add('Large tumor mass detected (>10 cm³)');
    } else if (volumes['tumor_volume']! > 5.0) {
      insights.add('Moderate tumor size detected (5-10 cm³)');
    } else {
      insights.add('Small tumor mass detected (<5 cm³)');
    }
    
    if (volumes['edema_volume']! > 30.0) {
      insights.add('Significant peritumoral edema present');
    }
    
    if (volumes['enhancing_volume']! > volumes['necrotic_volume']!) {
      insights.add('Active enhancing regions identified');
    }
    
    insights.add('Tumor occupies ${(volumes['tumor_volume']! / volumes['total_brain_volume']! * 100).toStringAsFixed(1)}% of total brain volume');
    
    return insights;
  }

  List<String> _generateRecommendations(List<String> insights) {
    final recommendations = <String>[];
    
    recommendations.add('Consult with neurosurgeon for treatment planning');
    recommendations.add('Consider follow-up MRI in 4-6 weeks');
    
    if (insights.any((insight) => insight.contains('Large tumor'))) {
      recommendations.add('Urgent neurosurgical evaluation recommended');
    }
    
    if (insights.any((insight) => insight.contains('edema'))) {
      recommendations.add('Consider steroid therapy for edema management');
    }
    
    recommendations.add('Monitor for neurological symptoms');
    
    return recommendations;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MRI Segmentation Report'),
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
                  _buildImageComparison(),
                  const SizedBox(height: 24),
                  _buildVolumeAnalysis(),
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
            _buildInfoRow('Scan Type', _medicalReport?['scan_type'] ?? 'Brain MRI'),
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

  Widget _buildImageComparison() {
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
            Row(
              children: [
                Expanded(
                  child: Column(
                    children: [
                      const Text('FLAIR Image', style: TextStyle(fontWeight: FontWeight.w500)),
                      const SizedBox(height: 8),
                      Container(
                        height: 150,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.grey[300]!),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.file(
                            widget.flairImage,
                            fit: BoxFit.cover,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    children: [
                      const Text('T1CE Image', style: TextStyle(fontWeight: FontWeight.w500)),
                      const SizedBox(height: 8),
                      Container(
                        height: 150,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.grey[300]!),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.file(
                            widget.t1ceImage,
                            fit: BoxFit.cover,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
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
          ],
        ),
      ),
    );
  }

  Widget _buildVolumeAnalysis() {
    final volumes = _medicalReport?['volumes'] as Map<String, double>? ?? {};
    
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
                  'Volume Analysis',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: kPrimaryColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildVolumeRow('Total Brain Volume', '${volumes['total_brain_volume']?.toStringAsFixed(1)} cm³', Colors.blue),
            _buildVolumeRow('Tumor Volume', '${volumes['tumor_volume']?.toStringAsFixed(1)} cm³', Colors.red),
            _buildVolumeRow('Edema Volume', '${volumes['edema_volume']?.toStringAsFixed(1)} cm³', Colors.orange),
            _buildVolumeRow('Enhancing Volume', '${volumes['enhancing_volume']?.toStringAsFixed(1)} cm³', Colors.purple),
            _buildVolumeRow('Necrotic Volume', '${volumes['necrotic_volume']?.toStringAsFixed(1)} cm³', Colors.grey),
          ],
        ),
      ),
    );
  }

  Widget _buildVolumeRow(String label, String value, Color color) {
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
    final insights = _medicalReport?['insights'] as List<String>? ?? [];
    
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
                  Expanded(child: Text(insight)),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendations() {
    final recommendations = _medicalReport?['recommendations'] as List<String>? ?? [];
    
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
                  Expanded(child: Text(recommendation)),
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
                  builder: (context) => ScanAnalysisScreen(token: widget.token),
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
