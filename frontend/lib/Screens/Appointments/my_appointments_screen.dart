import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';

class MyAppointmentsScreen extends StatefulWidget {
  final String token;
  final String email;
  final String userRole;

  const MyAppointmentsScreen({
    Key? key,
    required this.token,
    required this.email,
    required this.userRole,
  }) : super(key: key);

  @override
  _MyAppointmentsScreenState createState() => _MyAppointmentsScreenState();
}

class _MyAppointmentsScreenState extends State<MyAppointmentsScreen> {
  List<Map<String, dynamic>> appointments = [];
  bool isLoading = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadAppointments();
  }

  Future<void> _loadAppointments() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final appointmentService = AppointmentService(widget.token);
      final appointmentsList = await appointmentService.getMyAppointments();
      
      setState(() {
        appointments = appointmentsList;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        errorMessage = 'Failed to load appointments. Please try again.';
        isLoading = false;
      });
    }
  }

  String _formatDate(String dateString) {
    try {
      final date = DateTime.parse(dateString);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return dateString;
    }
  }

  String _formatTime(String timeString) {
    try {
      // Handle both "HH:MM" and "HH:MM:SS" formats
      final timeParts = timeString.split(':');
      final hour = int.parse(timeParts[0]);
      final minute = timeParts[1];
      
      String period = 'AM';
      int displayHour = hour;
      
      if (hour >= 12) {
        period = 'PM';
        if (hour > 12) {
          displayHour = hour - 12;
        }
      }
      if (hour == 0) {
        displayHour = 12;
      }
      
      return '$displayHour:$minute $period';
    } catch (e) {
      return timeString;
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'scheduled':
        return Colors.blue;
      case 'confirmed':
        return Colors.green;
      case 'cancelled':
        return Colors.red;
      case 'completed':
        return Colors.grey;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.userRole == 'doctor' ? 'My Appointments' : 'My Appointments',
          style: const TextStyle(color: Colors.white),
        ),
        backgroundColor: kPrimaryColor,
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAppointments,
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.error_outline,
                        size: 64,
                        color: Colors.red[300],
                      ),
                      const SizedBox(height: 16),
                      Text(
                        errorMessage!,
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.red,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadAppointments,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : appointments.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.calendar_today,
                            size: 64,
                            color: Colors.grey[400],
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'No appointments found',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey[600],
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            widget.userRole == 'doctor'
                                ? 'You don\'t have any scheduled appointments yet.'
                                : 'You haven\'t booked any appointments yet.',
                            style: TextStyle(
                              color: Colors.grey[500],
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadAppointments,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(defaultPadding),
                        itemCount: appointments.length,
                        itemBuilder: (context, index) {
                          final appointment = appointments[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: defaultPadding),
                            child: Padding(
                              padding: const EdgeInsets.all(defaultPadding),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Icon(
                                        Icons.calendar_today,
                                        color: kPrimaryColor,
                                        size: 20,
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        _formatDate(appointment['appointment_date']),
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const Spacer(),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 4,
                                        ),
                                        decoration: BoxDecoration(
                                          color: _getStatusColor(appointment['status']).withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: Text(
                                          appointment['status'].toUpperCase(),
                                          style: TextStyle(
                                            color: _getStatusColor(appointment['status']),
                                            fontSize: 12,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      Icon(
                                        Icons.access_time,
                                        color: Colors.grey[600],
                                        size: 16,
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        _formatTime(appointment['appointment_time']),
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: Colors.grey[700],
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  if (widget.userRole == 'doctor')
                                    Row(
                                      children: [
                                        Icon(
                                          Icons.person,
                                          color: Colors.grey[600],
                                          size: 16,
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          'Patient: ${appointment['patient_email']}',
                                          style: TextStyle(
                                            fontSize: 14,
                                            color: Colors.grey[700],
                                          ),
                                        ),
                                      ],
                                    )
                                  else
                                    Row(
                                      children: [
                                        Icon(
                                          Icons.medical_services,
                                          color: Colors.grey[600],
                                          size: 16,
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          'Doctor: ${appointment['doctor_email']}',
                                          style: TextStyle(
                                            fontSize: 14,
                                            color: Colors.grey[700],
                                          ),
                                        ),
                                      ],
                                    ),
                                  if (appointment['appointment_type'] != null)
                                    Padding(
                                      padding: const EdgeInsets.only(top: 8),
                                      child: Row(
                                        children: [
                                          Icon(
                                            Icons.category,
                                            color: Colors.grey[600],
                                            size: 16,
                                          ),
                                          const SizedBox(width: 8),
                                          Text(
                                            'Type: ${appointment['appointment_type']}',
                                            style: TextStyle(
                                              fontSize: 14,
                                              color: Colors.grey[700],
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  if (appointment['urgency_level'] != null)
                                    Padding(
                                      padding: const EdgeInsets.only(top: 4),
                                      child: Row(
                                        children: [
                                          Icon(
                                            Icons.priority_high,
                                            color: Colors.grey[600],
                                            size: 16,
                                          ),
                                          const SizedBox(width: 8),
                                          Text(
                                            'Urgency: ${appointment['urgency_level']}',
                                            style: TextStyle(
                                              fontSize: 14,
                                              color: Colors.grey[700],
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}


