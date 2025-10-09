import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';

class TimeSlotSelector extends StatefulWidget {
  final DateTime selectedDate;
  final String? doctorId;
  final String token;
  final Function(String) onTimeSlotSelected;

  const TimeSlotSelector({
    Key? key,
    required this.selectedDate,
    required this.doctorId,
    required this.token,
    required this.onTimeSlotSelected,
  }) : super(key: key);

  @override
  State<TimeSlotSelector> createState() => _TimeSlotSelectorState();
}

class _TimeSlotSelectorState extends State<TimeSlotSelector> {
  bool isLoading = false;
  List<String> timeSlots = [];
  String? errorMessage;
  String? selectedTimeSlot;

  @override
  void initState() {
    super.initState();
    _loadTimeSlots();
  }

  @override
  void didUpdateWidget(TimeSlotSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedDate != widget.selectedDate ||
        oldWidget.doctorId != widget.doctorId) {
      _loadTimeSlots();
    }
  }

  Future<void> _loadTimeSlots() async {
    if (widget.doctorId == null) return;

    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final appointmentService = AppointmentService(widget.token);
      // final dateStr = widget.selectedDate.toIso8601String().split('T')[0]; // YYYY-MM-DD format
      
      final response = await appointmentService.getAvailableTimeSlots(widget.doctorId!, widget.selectedDate);
      
      setState(() {
        timeSlots = response;
      });
    } catch (e) {
      setState(() {
        errorMessage = 'Failed to load time slots. Please try again.';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.doctorId == null) {
      return const Center(
        child: Text('Please select a doctor first'),
      );
    }

    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (errorMessage != null) {
      return Center(
        child: Column(
          children: [
            Text(errorMessage!, style: const TextStyle(color: Colors.red)),
            ElevatedButton(
              onPressed: _loadTimeSlots,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (timeSlots.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.schedule, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            const Text(
              'No available time slots',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'The doctor has not set availability for ${widget.selectedDate.toString().split(' ')[0]}',
              style: const TextStyle(
                color: Colors.grey,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadTimeSlots,
              child: const Text('Refresh'),
            ),
          ],
        ),
      );
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: timeSlots.map((timeSlot) {
        final isSelected = selectedTimeSlot == timeSlot;
        return ChoiceChip(
          label: Text(timeSlot),
          selected: isSelected,
          onSelected: (selected) {
            setState(() {
              selectedTimeSlot = selected ? timeSlot : null;
            });
            if (selected) {
              widget.onTimeSlotSelected(timeSlot);
            }
          },
          backgroundColor: kPrimaryLightColor,
          selectedColor: kPrimaryColor,
          labelStyle: TextStyle(
            color: isSelected ? Colors.white : kPrimaryColor,
          ),
        );
      }).toList(),
    );
  }
} 