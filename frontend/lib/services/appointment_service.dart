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
        headers: {'Authorization': 'Bearer $token'},
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
        headers: {'Authorization': 'Bearer $token'},
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

  Future<Map<String, dynamic>> bookAppointment({
    required String doctorId,
    required DateTime date,
    required String timeSlot, // This should now be in 24-hour format (HH:MM:SS)
    String? notes,
    required String patientEmail,
  }) async {
    try {
      // First verify if the slot is still available by getting real-time availability
      final slots = await getAvailableSlots(
        doctorEmail: doctorId,
        startDate: date,
      );

      // Now slots will only contain truly available slots (not booked)
      if (!slots.contains(timeSlot)) {
        throw Exception(
          'This time slot has just been booked. Please choose another available time.',
        );
      }

      final response = await http.post(
        Uri.parse('$baseUrl/appointments/create'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({
          'patient_email': patientEmail,
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
        final errorData = jsonDecode(response.body);
        final errorMessage =
            errorData['detail'] ?? 'Failed to book appointment';
        throw Exception(errorMessage);
      }
    } catch (e) {
      // Check if the error is from our slot verification
      if (e.toString().contains('no longer available')) {
        rethrow;
      }
      // For other errors, provide a more user-friendly message
      throw Exception(
        'Unable to book appointment. Please try again or choose another time slot.',
      );
    }
  }

  Future<List<String>> getAvailableSlots({
    required String doctorEmail,
    required DateTime startDate,
    DateTime? endDate,
  }) async {
    try {
      final startDateStr = startDate.toIso8601String().split('T')[0];
      final endDateStr = endDate?.toIso8601String().split('T')[0];

      String url =
          '$baseUrl/doctor-availability/available-slots/$doctorEmail?start_date=$startDateStr';
      if (endDateStr != null) {
        url += '&end_date=$endDateStr';
      }

      final response = await http.get(
        Uri.parse(url),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> slots = data['slots'] ?? [];
          return slots.cast<String>();
        } else {
          throw Exception(
            'Failed to get available slots: ${data['error'] ?? 'Unknown error'}',
          );
        }
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
        headers: {'Authorization': 'Bearer $token'},
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
        updateData['appointment_date'] =
            appointmentDate.toIso8601String().split('T')[0];
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

  Future<void> setWeeklySchedule(Map<String, dynamic> scheduleData) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/doctor-availability/set-weekly-schedule'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(scheduleData),
      );

      if (response.statusCode != 200) {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to set weekly schedule');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getDoctorAvailability() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/doctor-availability/my-weekly-schedule'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final schedule = data['schedule'];
          if (schedule == null) {
            // No schedule set yet, return empty list
            return <Map<String, dynamic>>[];
          }
          // Return the schedule as a single item list for compatibility
          return [schedule];
        } else {
          throw Exception(
            'Failed to get doctor availability: ${data['error'] ?? 'Unknown error'}',
          );
        }
      } else {
        throw Exception('Failed to get doctor availability');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  // ===== NEW DAILY ADJUSTMENTS & BLOCK TIME METHODS =====

  Future<Map<String, dynamic>> getDayView(
    String doctorEmail,
    DateTime viewDate,
  ) async {
    try {
      final dateStr = viewDate.toIso8601String().split('T')[0];
      final response = await http.get(
        Uri.parse(
          '$baseUrl/doctor-availability/day-view/$doctorEmail?view_date=$dateStr',
        ),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data['day_view'];
        } else {
          throw Exception(
            'Failed to get day view: ${data['error'] ?? 'Unknown error'}',
          );
        }
      } else {
        throw Exception('Failed to get day view');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<void> createDailyOverride(
    String doctorEmail,
    Map<String, dynamic> overrideData,
  ) async {
    try {
      final response = await http.post(
        Uri.parse(
          '$baseUrl/doctor-availability/create-daily-override?doctor_email=$doctorEmail',
        ),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(overrideData),
      );

      if (response.statusCode != 200) {
        final errorData = jsonDecode(response.body);
        throw Exception(
          errorData['detail'] ?? 'Failed to create daily override',
        );
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<void> addBlockTime(
    String doctorEmail,
    DateTime blockDate,
    Map<String, dynamic> blockTimeData,
  ) async {
    try {
      final dateStr = blockDate.toIso8601String().split('T')[0];
      final response = await http.post(
        Uri.parse(
          '$baseUrl/doctor-availability/add-block-time?doctor_email=$doctorEmail&block_date=$dateStr',
        ),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(blockTimeData),
      );

      if (response.statusCode != 200) {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['detail'] ?? 'Failed to add block time');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<void> deleteDailyOverride(
    String doctorEmail,
    DateTime overrideDate,
  ) async {
    try {
      final dateStr = overrideDate.toIso8601String().split('T')[0];
      final response = await http.delete(
        Uri.parse(
          '$baseUrl/doctor-availability/delete-daily-override/$doctorEmail?override_date=$dateStr',
        ),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode != 200) {
        final errorData = jsonDecode(response.body);
        throw Exception(
          errorData['detail'] ?? 'Failed to delete daily override',
        );
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getAvailableSlotsWithOverrides({
    required String doctorEmail,
    required DateTime startDate,
    DateTime? endDate,
  }) async {
    try {
      final startDateStr = startDate.toIso8601String().split('T')[0];
      final endDateStr = endDate?.toIso8601String().split('T')[0];

      String url =
          '$baseUrl/doctor-availability/available-slots-with-overrides/$doctorEmail?start_date=$startDateStr';
      if (endDateStr != null) {
        url += '&end_date=$endDateStr';
      }

      final response = await http.get(
        Uri.parse(url),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> slots = data['slots'] ?? [];
          return slots.cast<Map<String, dynamic>>();
        } else {
          throw Exception(
            'Failed to get available slots with overrides: ${data['error'] ?? 'Unknown error'}',
          );
        }
      } else {
        throw Exception('Failed to get available slots with overrides');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }

  Future<List<String>> getBlockTimeReasons() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/doctor-availability/block-time-reasons'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> reasons = data['reasons'] ?? [];
          return reasons.cast<String>();
        } else {
          throw Exception(
            'Failed to get block time reasons: ${data['error'] ?? 'Unknown error'}',
          );
        }
      } else {
        throw Exception('Failed to get block time reasons');
      }
    } catch (e) {
      throw Exception('Error: $e');
    }
  }
}
