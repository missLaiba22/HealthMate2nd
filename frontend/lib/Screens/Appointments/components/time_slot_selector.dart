import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';

class TimeSlotSelector extends StatefulWidget {
  final DateTime selectedDate;
  final String? doctorId;
  final Function(String) onTimeSlotSelected;

  const TimeSlotSelector({
    Key? key,
    required this.selectedDate,
    required this.doctorId,
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
      // TODO: Replace with actual API call
      // Simulated data for now
      await Future.delayed(const Duration(seconds: 1));
      setState(() {
        timeSlots = [
          '09:00 AM',
          '10:00 AM',
          '11:00 AM',
          '02:00 PM',
          '03:00 PM',
          '04:00 PM',
        ];
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