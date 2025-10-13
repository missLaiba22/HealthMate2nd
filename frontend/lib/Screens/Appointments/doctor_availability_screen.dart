import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';
import 'day_view_editor_screen.dart';

class DoctorAvailabilityScreen extends StatefulWidget {
  final String token;
  final String email;

  const DoctorAvailabilityScreen({
    Key? key,
    required this.token,
    required this.email,
  }) : super(key: key);

  @override
  State<DoctorAvailabilityScreen> createState() => _DoctorAvailabilityScreenState();
}

class _DoctorAvailabilityScreenState extends State<DoctorAvailabilityScreen> {
  late AppointmentService _appointmentService;
  bool _isLoading = false;
  String? _errorMessage;
  Map<String, dynamic>? _weeklySchedule;
  bool _hasSchedule = false;

  final List<String> _daysOfWeek = [
    'Monday',
    'Tuesday', 
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
  ];

  final List<String> _dayKeys = [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday'
  ];

  @override
  void initState() {
    super.initState();
    _appointmentService = AppointmentService(widget.token);
    _loadWeeklySchedule();
  }

  Future<void> _loadWeeklySchedule() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final availabilityList = await _appointmentService.getDoctorAvailability();
      
      setState(() {
        _hasSchedule = availabilityList.isNotEmpty;
        if (_hasSchedule) {
          // Use the weekly schedule directly from the backend
          _weeklySchedule = availabilityList.first;
        } else {
          _weeklySchedule = _createEmptySchedule();
        }
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load weekly schedule: $e';
        _weeklySchedule = _createEmptySchedule();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Map<String, dynamic> _createEmptySchedule() {
    return {
      'doctor_email': widget.email,
      'monday': null,
      'tuesday': null,
      'wednesday': null,
      'thursday': null,
      'friday': null,
      'saturday': null,
      'sunday': null,
      'slot_duration_minutes': 30,
    };
  }

  // Removed _convertToWeeklySchedule method - now using direct weekly schedule format

  Future<void> _saveWeeklySchedule() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // Convert to the format expected by the backend
      final scheduleData = {
        'doctor_email': widget.email,
        'monday': _weeklySchedule!['monday'],
        'tuesday': _weeklySchedule!['tuesday'],
        'wednesday': _weeklySchedule!['wednesday'],
        'thursday': _weeklySchedule!['thursday'],
        'friday': _weeklySchedule!['friday'],
        'saturday': _weeklySchedule!['saturday'],
        'sunday': _weeklySchedule!['sunday'],
        'slot_duration_minutes': _weeklySchedule!['slot_duration_minutes'] ?? 30,
      };

      await _appointmentService.setWeeklySchedule(scheduleData);
      
      setState(() {
        _hasSchedule = true;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Weekly schedule saved successfully!'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to save weekly schedule: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _toggleDayAvailability(int dayIndex) {
    final dayKey = _dayKeys[dayIndex];
    setState(() {
      if (_weeklySchedule![dayKey] == null) {
        // Enable the day with default times
        _weeklySchedule![dayKey] = {
          'start_time': '09:00:00',
          'end_time': '17:00:00',
          'is_available': true,
        };
      } else {
        // Disable the day
        _weeklySchedule![dayKey] = null;
      }
    });
  }

  void _updateDayTime(int dayIndex, String timeType, String time) {
    final dayKey = _dayKeys[dayIndex];
    if (_weeklySchedule![dayKey] != null) {
      setState(() {
        _weeklySchedule![dayKey][timeType] = time;
      });
    }
  }

  void _navigateToDayViewEditor() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => DayViewEditorScreen(
          token: widget.token,
          doctorEmail: widget.email,
          selectedDate: DateTime.now(),
        ),
      ),
    ).then((_) {
      // Refresh the weekly schedule when returning
      _loadWeeklySchedule();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Weekly Availability'),
        backgroundColor: kPrimaryColor,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadWeeklySchedule,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? _buildErrorWidget()
              : _buildWeeklyScheduleWidget(),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton(
            onPressed: _navigateToDayViewEditor,
            backgroundColor: Colors.blue,
            heroTag: "day_view",
            child: const Icon(Icons.calendar_today, color: Colors.white),
          ),
          const SizedBox(height: 8),
          FloatingActionButton(
            onPressed: _saveWeeklySchedule,
            backgroundColor: kPrimaryColor,
            heroTag: "save",
            child: const Icon(Icons.save, color: Colors.white),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            size: 64,
            color: Colors.red,
          ),
          const SizedBox(height: 16),
          Text(
            _errorMessage!,
            style: const TextStyle(fontSize: 16),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadWeeklySchedule,
            child: const Text('Try Again'),
          ),
        ],
      ),
    );
  }

  Widget _buildWeeklyScheduleWidget() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Set Your Weekly Availability',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Configure your availability for each day of the week. This schedule will be used to generate appointment slots.',
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      const Text('Slot Duration: '),
                      DropdownButton<int>(
                        value: _weeklySchedule!['slot_duration_minutes'] ?? 30,
                        items: [15, 30, 45, 60].map((duration) {
                          return DropdownMenuItem(
                            value: duration,
                            child: Text('$duration minutes'),
                          );
                        }).toList(),
                        onChanged: (value) {
                          setState(() {
                            _weeklySchedule!['slot_duration_minutes'] = value;
                          });
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          ...List.generate(7, (index) => _buildDayCard(index)),
        ],
      ),
    );
  }

  Widget _buildDayCard(int dayIndex) {
    final dayName = _daysOfWeek[dayIndex];
    final dayKey = _dayKeys[dayIndex];
    final dayData = _weeklySchedule![dayKey];
    final isEnabled = dayData != null;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    dayName,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Switch(
                  value: isEnabled,
                  onChanged: (_) => _toggleDayAvailability(dayIndex),
                  activeColor: kPrimaryColor,
                ),
              ],
            ),
            if (isEnabled) ...[
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Start Time'),
                        const SizedBox(height: 4),
                        TextFormField(
                          initialValue: dayData['start_time'] ?? '09:00:00',
                          decoration: const InputDecoration(
                            hintText: 'HH:MM',
                            border: OutlineInputBorder(),
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          ),
                          onChanged: (value) => _updateDayTime(dayIndex, 'start_time', value),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('End Time'),
                        const SizedBox(height: 4),
                        TextFormField(
                          initialValue: dayData['end_time'] ?? '17:00:00',
                          decoration: const InputDecoration(
                            hintText: 'HH:MM',
                            border: OutlineInputBorder(),
                            contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          ),
                          onChanged: (value) => _updateDayTime(dayIndex, 'end_time', value),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}