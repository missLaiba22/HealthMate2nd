import 'package:flutter/material.dart';

const kPrimaryColor = Color(0xFF2196F3);
const kPrimaryLightColor = Color(0xFFE3F2FD);

const double defaultPadding = 16.0;

class ApiConfig {
  // Override at run time with: --dart-define=BASE_URL=http://<ip>:8000
  static const String baseUrl = String.fromEnvironment(
    'BASE_URL',
    defaultValue: 'http://192.168.0.146:8000',
  );
}
