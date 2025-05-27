import 'dart:convert';
import 'package:http/http.dart' as http;
import '../constants.dart';

class AppointmentService {
  final String token;
  final String baseUrl = ApiConfig.baseUrl;

  AppointmentService(this.token);

  Future<List<Map<String, dynamic>>> getAvailableDoctors() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/appointments/doctors'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to load doctors');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<List<String>> getAvailableTimeSlots(String doctorId, DateTime date) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/appointments/time-slots?doctor_id=$doctorId&date=${date.toIso8601String()}'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<String>();
      } else {
        throw Exception('Failed to load time slots');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<void> bookAppointment({
    required String doctorId,
    required DateTime date,
    required String timeSlot,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/appointments/book'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'doctor_id': doctorId,
          'date': date.toIso8601String(),
          'time_slot': timeSlot,
        }),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to book appointment');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getMyAppointments() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/appointments/my-appointments'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to load appointments');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<void> cancelAppointment(String appointmentId) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/appointments/$appointmentId'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to cancel appointment');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
} 