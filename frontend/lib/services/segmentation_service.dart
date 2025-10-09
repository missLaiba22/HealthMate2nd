import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

class SegmentationApiService {
  final String baseUrl;
  SegmentationApiService({required this.baseUrl});

  Future<Map<String, dynamic>> segmentTwoModalities({
    required String flairBase64,
    required String t1ceBase64,
  }) async {
    final uri = Uri.parse('$baseUrl/scan/segment/two-modalities');
    final resp = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
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


