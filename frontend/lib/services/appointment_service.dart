import 'dart:convert';
import 'package:http/http.dart' as http;
import '../constants.dart';

class AppointmentService {
  final String token;
  final String baseUrl = ApiConfig.baseUrl;

  AppointmentService(this.token);

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
        throw Exception('Failed to fetch appointments');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getDoctors() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/appointments/doctors'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to fetch doctors');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // Alias method for backward compatibility
  Future<List<Map<String, dynamic>>> getAvailableDoctors() async {
    return await getDoctors();
  }

  Future<List<String>> getTimeSlots({
    required String doctorEmail,
    required DateTime date,
  }) async {
    try {
      final dateStr = date.toIso8601String().split('T')[0];
      final response = await http.get(
        Uri.parse('$baseUrl/appointments/time-slots?doctor_email=$doctorEmail&date=$dateStr'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<dynamic> timeSlots = data['time_slots'] ?? [];
        return timeSlots.cast<String>();
      } else {
        throw Exception('Failed to fetch time slots');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // Alias method for backward compatibility
  Future<List<String>> getAvailableTimeSlots(String doctorId, DateTime date) async {
    return await getTimeSlots(doctorEmail: doctorId, date: date);
  }

  Future<Map<String, dynamic>> bookAppointment({
    required String doctorId,
    required DateTime date,
    required String timeSlot,
    String? notes,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/appointments/create'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'patient_email': '', // Will be filled by backend from token
          'doctor_email': doctorId,
          'appointment_date': date.toIso8601String().split('T')[0],
          'appointment_time': timeSlot,
          'appointment_type': 'consultation',
          'notes': notes,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to book appointment');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<Map<String, dynamic>> createAppointment({
    required String doctorEmail,
    required DateTime appointmentDate,
    required String appointmentTime,
    String appointmentType = 'consultation',
    String? notes,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/appointments/create'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'patient_email': '', // Will be filled by backend from token
          'doctor_email': doctorEmail,
          'appointment_date': appointmentDate.toIso8601String().split('T')[0],
          'appointment_time': appointmentTime,
          'appointment_type': appointmentType,
          'notes': notes,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to create appointment');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getAvailableSlots({
    required String doctorEmail,
    required DateTime startDate,
    DateTime? endDate,
  }) async {
    try {
      final startDateStr = startDate.toIso8601String().split('T')[0];
      final endDateStr = endDate?.toIso8601String().split('T')[0];
      
      String url = '$baseUrl/appointments/slots/$doctorEmail?start_date=$startDateStr';
      if (endDateStr != null) {
        url += '&end_date=$endDateStr';
      }

      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        return data.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get available slots');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<bool> cancelAppointment(String appointmentId) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/appointments/$appointmentId'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<Map<String, dynamic>> updateAppointment({
    required String appointmentId,
    DateTime? appointmentDate,
    String? appointmentTime,
    int? durationMinutes,
    String? status,
    String? notes,
  }) async {
    try {
      final Map<String, dynamic> updateData = {};
      
      if (appointmentDate != null) {
        updateData['appointment_date'] = appointmentDate.toIso8601String().split('T')[0];
      }
      if (appointmentTime != null) {
        updateData['appointment_time'] = appointmentTime;
      }
      if (durationMinutes != null) {
        updateData['duration_minutes'] = durationMinutes;
      }
      if (status != null) {
        updateData['status'] = status;
      }
      if (notes != null) {
        updateData['notes'] = notes;
      }

      final response = await http.put(
        Uri.parse('$baseUrl/appointments/$appointmentId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(updateData),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to update appointment');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<void> setDoctorAvailability({
    required String doctorEmail,
    required int dayOfWeek,
    required String startTime,
    required String endTime,
    bool isAvailable = true,
    int maxAppointmentsPerSlot = 1,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/appointments/availability'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'doctor_email': doctorEmail,
          'day_of_week': dayOfWeek,
          'start_time': startTime,
          'end_time': endTime,
          'is_available': isAvailable,
          'max_appointments_per_slot': maxAppointmentsPerSlot,
        }),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to set availability');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // TODO: Implement delete availability endpoint in backend
  // Future<void> deleteDoctorAvailability({
  //   required String availabilityDate, // YYYY-MM-DD format
  // }) async {
  //   try {
  //     final response = await http.delete(
  //       Uri.parse('$baseUrl/appointments/availability?availability_date=$availabilityDate'),
  //       headers: {
  //         'Content-Type': 'application/json',
  //         'Authorization': 'Bearer $token',
  //       },
  //     );

  //     if (response.statusCode != 200) {
  //       throw Exception('Failed to delete availability');
  //     }
  //   } catch (e) {
  //     throw Exception('Error: $e');
  //   }
  // }

  Future<List<Map<String, dynamic>>> getDoctorAvailability() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/appointments/my-availability'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<dynamic> availabilityRecords = data['availability_records'] ?? [];
        return availabilityRecords.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to get doctor availability');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
}