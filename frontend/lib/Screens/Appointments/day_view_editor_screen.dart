import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';
import 'components/calendar_date_picker.dart';

class DayViewEditorScreen extends StatefulWidget {
  final String token;
  final String doctorEmail;
  final DateTime selectedDate;

  const DayViewEditorScreen({
    Key? key,
    required this.token,
    required this.doctorEmail,
    required this.selectedDate,
  }) : super(key: key);

  @override
  State<DayViewEditorScreen> createState() => _DayViewEditorScreenState();
}

class _DayViewEditorScreenState extends State<DayViewEditorScreen> {
  late AppointmentService _appointmentService;
  bool _isLoading = false;
  String? _errorMessage;
  Map<String, dynamic>? _dayView;
  bool _hasOverride = false;
  List<Map<String, dynamic>> _blockTimes = [];
  late DateTime _currentSelectedDate;
  
  // Form controllers
  final _startTimeController = TextEditingController();
  final _endTimeController = TextEditingController();
  final _reasonController = TextEditingController();
  String _selectedReason = 'lunch';
  
  final List<String> _blockReasons = [
    'lunch',
    'surgery', 
    'personal',
    'meeting',
    'emergency',
    'break',
    'training',
    'other'
  ];

  @override
  void initState() {
    super.initState();
    _appointmentService = AppointmentService(widget.token);
    _currentSelectedDate = widget.selectedDate;
    _loadDayView();
  }

  @override
  void dispose() {
    _startTimeController.dispose();
    _endTimeController.dispose();
    _reasonController.dispose();
    super.dispose();
  }

  Future<void> _loadDayView() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final dayView = await _appointmentService.getDayView(
        widget.doctorEmail, 
        _currentSelectedDate
      );
      
      setState(() {
        _dayView = dayView;
        _hasOverride = dayView['has_override'] ?? false;
        _blockTimes = List<Map<String, dynamic>>.from(
          dayView['daily_override']?['block_time_slots'] ?? []
        );
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load day view: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _addBlockTime() async {
    if (_startTimeController.text.isEmpty || _endTimeController.text.isEmpty) {
      _showErrorSnackBar('Please fill in start and end times');
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final blockTimeData = {
        'start_time': _startTimeController.text,
        'end_time': _endTimeController.text,
        'reason': _selectedReason,
        'description': _reasonController.text.isEmpty ? null : _reasonController.text,
      };

      await _appointmentService.addBlockTime(
        widget.doctorEmail,
        _currentSelectedDate,
        blockTimeData
      );

      // Clear form
      _startTimeController.clear();
      _endTimeController.clear();
      _reasonController.clear();
      _selectedReason = 'lunch';

      // Reload day view
      await _loadDayView();

      _showSuccessSnackBar('Block time added successfully!');
    } catch (e) {
      _showErrorSnackBar('Failed to add block time: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _createDailyOverride() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final overrideData = {
        'override_date': _currentSelectedDate.toIso8601String().split('T')[0],
        'is_available': true,
        'start_time': _startTimeController.text.isEmpty ? null : _startTimeController.text,
        'end_time': _endTimeController.text.isEmpty ? null : _endTimeController.text,
        'override_reason': _reasonController.text.isEmpty ? null : _reasonController.text,
        'block_time_slots': _blockTimes.map((bt) => {
          'start_time': bt['start_time'],
          'end_time': bt['end_time'],
          'reason': bt['reason'],
          'description': bt['description'],
        }).toList(),
      };

      await _appointmentService.createDailyOverride(
        widget.doctorEmail,
        overrideData
      );

      await _loadDayView();
      _showSuccessSnackBar('Daily override created successfully!');
    } catch (e) {
      _showErrorSnackBar('Failed to create daily override: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _deleteDailyOverride() async {
    setState(() {
      _isLoading = true;
    });

    try {
      await _appointmentService.deleteDailyOverride(
        widget.doctorEmail,
        _currentSelectedDate
      );

      await _loadDayView();
      _showSuccessSnackBar('Daily override deleted successfully!');
    } catch (e) {
      _showErrorSnackBar('Failed to delete daily override: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _onDateSelected(DateTime selectedDate) {
    setState(() {
      _currentSelectedDate = selectedDate;
    });
    _loadDayView();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Day View - ${_currentSelectedDate.toString().split(' ')[0]}'),
        backgroundColor: kPrimaryColor,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDayView,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? _buildErrorWidget()
              : _buildDayViewWidget(),
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
            onPressed: _loadDayView,
            child: const Text('Try Again'),
          ),
        ],
      ),
    );
  }

  Widget _buildDayViewWidget() {
    if (_dayView == null) {
      return const Center(child: Text('No data available'));
    }

    final computedAvailability = _dayView!['computed_availability'] ?? {};
    final weeklySchedule = _dayView!['weekly_schedule'];
    final existingSlots = List<Map<String, dynamic>>.from(
      _dayView!['existing_slots'] ?? []
    );

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Date Selection
          CustomCalendarDatePicker(
            selectedDate: _currentSelectedDate,
            onDateSelected: _onDateSelected,
          ),
          const SizedBox(height: 16),
          
          // Quick Date Selection
          QuickDateSelector(
            selectedDate: _currentSelectedDate,
            onDateSelected: _onDateSelected,
          ),
          const SizedBox(height: 16),
          
          // Day Overview Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${_currentSelectedDate.toString().split(' ')[0]} - ${_dayView!['day_name']}',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(
                        computedAvailability['is_available'] 
                            ? Icons.check_circle 
                            : Icons.cancel,
                        color: computedAvailability['is_available'] 
                            ? Colors.green 
                            : Colors.red,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        computedAvailability['is_available'] 
                            ? 'Available' 
                            : 'Not Available',
                        style: TextStyle(
                          color: computedAvailability['is_available'] 
                              ? Colors.green 
                              : Colors.red,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                  if (computedAvailability['start_time'] != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Time: ${computedAvailability['start_time']} - ${computedAvailability['end_time']}',
                      style: const TextStyle(color: Colors.grey),
                    ),
                  ],
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Weekly Schedule Info
          if (weeklySchedule != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Weekly Schedule',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Default schedule for ${_dayView!['day_name']}s',
                      style: const TextStyle(color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
          
          // Block Time Management
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Block Time Management',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Add Block Time Form
                  Row(
                    children: [
                      Expanded(
                        flex: 2,
                        child: TextFormField(
                          controller: _startTimeController,
                          decoration: const InputDecoration(
                            labelText: 'Start Time',
                            hintText: 'HH:MM',
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        flex: 2,
                        child: TextFormField(
                          controller: _endTimeController,
                          decoration: const InputDecoration(
                            labelText: 'End Time',
                            hintText: 'HH:MM',
                            border: OutlineInputBorder(),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  
                  DropdownButtonFormField<String>(
                    value: _selectedReason,
                    decoration: const InputDecoration(
                      labelText: 'Reason',
                      border: OutlineInputBorder(),
                    ),
                    items: _blockReasons.map((reason) {
                      return DropdownMenuItem(
                        value: reason,
                        child: Text(reason.toUpperCase()),
                      );
                    }).toList(),
                    onChanged: (value) {
                      setState(() {
                        _selectedReason = value!;
                      });
                    },
                  ),
                  const SizedBox(height: 8),
                  
                  TextFormField(
                    controller: _reasonController,
                    decoration: const InputDecoration(
                      labelText: 'Description (Optional)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  ElevatedButton(
                    onPressed: _addBlockTime,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: kPrimaryColor,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Add Block Time'),
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Existing Block Times
          if (_blockTimes.isNotEmpty) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Existing Block Times',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ..._blockTimes.map((blockTime) => ListTile(
                      leading: Icon(
                        Icons.block,
                        color: Colors.red,
                      ),
                      title: Text(
                        '${blockTime['start_time']} - ${blockTime['end_time']}',
                      ),
                      subtitle: Text(
                        '${blockTime['reason']}${blockTime['description'] != null ? ': ${blockTime['description']}' : ''}',
                      ),
                    )).toList(),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
          
          // Existing Appointments
          if (existingSlots.isNotEmpty) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Existing Appointments',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ...existingSlots.map((slot) => ListTile(
                      leading: Icon(
                        slot['is_available'] 
                            ? Icons.schedule 
                            : Icons.person,
                        color: slot['is_available'] 
                            ? Colors.green 
                            : Colors.blue,
                      ),
                      title: Text(slot['slot_time']),
                      subtitle: Text(
                        slot['is_available'] 
                            ? 'Available' 
                            : 'Booked${slot['appointment_id'] != null ? ' (${slot['appointment_id']})' : ''}',
                      ),
                    )).toList(),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
          
          // Action Buttons
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: _createDailyOverride,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Update Day'),
                ),
              ),
              if (_hasOverride) ...[
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _deleteDailyOverride,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Delete Override'),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}
