import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

class SegmentationApiService {
  final String baseUrl;
  final String? token;
  SegmentationApiService({required this.baseUrl, this.token});

  Future<Map<String, dynamic>> segmentTwoModalities({
    required String flairBase64,
    required String t1ceBase64,
  }) async {
    final uri = Uri.parse('$baseUrl/scan/segment/two-modalities');
    
    // Prepare headers with authorization if token is provided
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    
    final resp = await http.post(
      uri,
      headers: headers,
      body: jsonEncode({
        'flair_image': flairBase64,
        't1ce_image': t1ceBase64,
      }),
    );
    if (resp.statusCode != 200) {
      throw Exception('Segmentation failed: ${resp.statusCode} ${resp.body}');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  static Uint8List decodeBase64Image(String b64) {
    return base64Decode(b64);
  }
}


