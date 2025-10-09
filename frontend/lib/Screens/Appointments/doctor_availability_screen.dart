import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';

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
  final List<Map<String, dynamic>> _availabilitySchedule = [];
  bool _isLoading = false;
  String? _errorMessage;

  final List<String> _daysOfWeek = [
    'Monday',
    'Tuesday', 
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
  ];

  @override
  void initState() {
    super.initState();
    _appointmentService = AppointmentService(widget.token);
    _loadExistingAvailability();
  }

  Future<void> _loadExistingAvailability() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final availabilityList = await _appointmentService.getDoctorAvailability();

      // Filter out records without availability_date and sort by date
      final validAvailability = availabilityList
          .where((availability) => availability['availability_date'] != null)
          .toList();
      
      // Sort by date (newest first)
      validAvailability.sort((a, b) {
        try {
          final dateA = DateTime.parse(a['availability_date']);
          final dateB = DateTime.parse(b['availability_date']);
          return dateB.compareTo(dateA);
        } catch (e) {
          return 0;
        }
      });

      setState(() {
        _availabilitySchedule.clear();
        _availabilitySchedule.addAll(validAvailability);
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load existing availability: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Set Availability'),
        backgroundColor: kPrimaryColor,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadExistingAvailability,
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _showAddAvailabilityDialog,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? _buildErrorWidget()
              : _buildContent(),
    );
  }

  Widget _buildErrorWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text(
            _errorMessage!,
            style: const TextStyle(color: Colors.red, fontSize: 16),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _errorMessage = null;
              });
            },
            child: const Text('Try Again'),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    return _availabilitySchedule.isEmpty
        ? _buildEmptyState()
        : ListView.builder(
            padding: const EdgeInsets.all(defaultPadding),
            itemCount: _availabilitySchedule.length,
            itemBuilder: (context, index) {
              final availability = _availabilitySchedule[index];
              return _buildAvailabilityCard(availability, index);
            },
          );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.schedule, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          const Text(
            'No availability set',
            style: TextStyle(fontSize: 18, color: Colors.grey),
          ),
          const SizedBox(height: 8),
          const Text(
            'Add your availability schedule to start receiving appointments',
            style: TextStyle(color: Colors.grey),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _showAddAvailabilityDialog,
            icon: const Icon(Icons.add),
            label: const Text('Add Availability'),
            style: ElevatedButton.styleFrom(
              backgroundColor: kPrimaryColor,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAvailabilityCard(Map<String, dynamic> availability, int index) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(defaultPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.calendar_today, color: kPrimaryColor),
                const SizedBox(width: 8),
                Text(
                  availability['availability_date'] ?? 'Unknown Date',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.red),
                  onPressed: () => _removeAvailability(index),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.access_time, size: 16, color: Colors.grey),
                const SizedBox(width: 8),
                Text('${availability['start_time']} - ${availability['end_time']}'),
                const SizedBox(width: 16),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: availability['is_available'] ? Colors.green : Colors.red,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    availability['is_available'] ? 'Available' : 'Unavailable',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Max appointments per slot: ${availability['max_appointments_per_slot']}',
              style: const TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  void _showAddAvailabilityDialog() {
    showDialog(
      context: context,
      builder: (context) => _AddAvailabilityDialog(
        onAdd: _addAvailability,
        daysOfWeek: _daysOfWeek,
      ),
    );
  }

  void _addAvailability(Map<String, dynamic> availability) {
    setState(() {
      _availabilitySchedule.add(availability);
    });
    _saveAvailability(availability);
  }

  Future<void> _removeAvailability(int index) async {
    final availability = _availabilitySchedule[index];
    
    // Show confirmation dialog
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Delete Availability'),
          content: Text(
            'Are you sure you want to delete availability for ${availability['availability_date']}?'
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: TextButton.styleFrom(foregroundColor: Colors.red),
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );

    if (confirm != true) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // TODO: Implement delete availability endpoint in backend
      // For now, just remove from local state
      // await _appointmentService.deleteDoctorAvailability(
      //   availabilityDate: availability['availability_date'],
      // );

      // Remove from local state only after successful API call
      setState(() {
        _availabilitySchedule.removeAt(index);
        _isLoading = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Availability deleted successfully'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to delete availability: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _saveAvailability(Map<String, dynamic> availability) async {
    setState(() {
      _isLoading = true;
    });

    try {
      // Convert date to day of week (0=Monday, 6=Sunday)
      DateTime date = DateTime.parse(availability['availability_date']);
      int dayOfWeek = date.weekday - 1; // Convert to 0-6 format
      
      await _appointmentService.setDoctorAvailability(
        doctorEmail: widget.email,
        dayOfWeek: dayOfWeek,
        startTime: availability['start_time'],
        endTime: availability['end_time'],
        isAvailable: availability['is_available'],
        maxAppointmentsPerSlot: availability['max_appointments_per_slot'],
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Availability saved successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        // Reload the availability list to show the saved item
        _loadExistingAvailability();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Failed to save availability: $e';
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to save availability: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
}

class _AddAvailabilityDialog extends StatefulWidget {
  final Function(Map<String, dynamic>) onAdd;
  final List<String> daysOfWeek;

  const _AddAvailabilityDialog({
    required this.onAdd,
    required this.daysOfWeek,
  });

  @override
  State<_AddAvailabilityDialog> createState() => _AddAvailabilityDialogState();
}

class _AddAvailabilityDialogState extends State<_AddAvailabilityDialog> {
  DateTime _selectedDate = DateTime.now();
  TimeOfDay _startTime = const TimeOfDay(hour: 9, minute: 0);
  TimeOfDay _endTime = const TimeOfDay(hour: 17, minute: 0);
  bool _isAvailable = true;
  int _maxAppointments = 1;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Availability'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            InkWell(
              onTap: _selectDate,
              child: InputDecorator(
                decoration: const InputDecoration(
                  labelText: 'Select Date',
                  border: OutlineInputBorder(),
                  suffixIcon: Icon(Icons.calendar_today),
                ),
                child: Text(
                  '${_selectedDate.day}/${_selectedDate.month}/${_selectedDate.year}',
                  style: const TextStyle(fontSize: 16),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ListTile(
                    title: const Text('Start Time'),
                    subtitle: Text(_startTime.format(context)),
                    onTap: _selectStartTime,
                  ),
                ),
                Expanded(
                  child: ListTile(
                    title: const Text('End Time'),
                    subtitle: Text(_endTime.format(context)),
                    onTap: _selectEndTime,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Available'),
              subtitle: const Text('Toggle availability for this day'),
              value: _isAvailable,
              onChanged: (value) {
                setState(() {
                  _isAvailable = value;
                });
              },
            ),
            if (_isAvailable) ...[
              const SizedBox(height: 16),
              TextFormField(
                initialValue: _maxAppointments.toString(),
                decoration: const InputDecoration(
                  labelText: 'Max Appointments per Slot',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                onChanged: (value) {
                  setState(() {
                    _maxAppointments = int.tryParse(value) ?? 1;
                  });
                },
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _saveAvailability,
          child: const Text('Save'),
        ),
      ],
    );
  }

  Future<void> _selectStartTime() async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: _startTime,
    );
    if (picked != null) {
      setState(() {
        _startTime = picked;
      });
    }
  }

  Future<void> _selectEndTime() async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: _endTime,
    );
    if (picked != null) {
      setState(() {
        _endTime = picked;
      });
    }
  }

  Future<void> _selectDate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  void _saveAvailability() {
    final availability = {
      'availability_date': '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
      'start_time': '${_startTime.hour.toString().padLeft(2, '0')}:${_startTime.minute.toString().padLeft(2, '0')}',
      'end_time': '${_endTime.hour.toString().padLeft(2, '0')}:${_endTime.minute.toString().padLeft(2, '0')}',
      'is_available': _isAvailable,
      'max_appointments_per_slot': _maxAppointments,
    };

    widget.onAdd(availability);
    Navigator.pop(context);
  }
}





