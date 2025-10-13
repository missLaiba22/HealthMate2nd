import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';
import 'dart:async';

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
  Map<String, String> timeSlots = {}; // Display format -> Backend format
  String? errorMessage;
  String? selectedDisplayTime;
  Timer? _debounceTimer;
  int _retryAttempts = 0;
  static const int maxRetries = 2;

  @override
  void initState() {
    super.initState();
    if (widget.doctorId != null) {
      Future.microtask(() => _loadTimeSlots());
    }
  }

  @override
  void didUpdateWidget(TimeSlotSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedDate != widget.selectedDate ||
        oldWidget.doctorId != widget.doctorId) {
      if (widget.doctorId != null) {
        Future.microtask(() => _loadTimeSlots());
      }
    }
  }

  Future<void> _loadTimeSlots() async {
    if (widget.doctorId == null) return;

    // Cancel any pending debounce timer
    _debounceTimer?.cancel();

    // Set loading state only if this is the first attempt
    if (_retryAttempts == 0) {
      setState(() {
        isLoading = true;
        errorMessage = null;
      });
    }

    // Create a new debounce timer
    _debounceTimer = Timer(const Duration(milliseconds: 300), () async {
      try {
        final appointmentService = AppointmentService(widget.token);
        final timeStrings = await appointmentService.getAvailableSlots(
          doctorEmail: widget.doctorId!,
          startDate: widget.selectedDate,
        );

        print("DEBUG: Received slots: $timeStrings");

        // If we get an empty list and haven't exceeded retries, retry after a delay
        if (timeStrings.isEmpty && _retryAttempts < maxRetries) {
          _retryAttempts++;
          // Increase delay for first retry, use shorter delay for subsequent retries
          final delay = _retryAttempts == 1 ? 1000 : 500;
          await Future.delayed(Duration(milliseconds: delay));
          if (mounted) {
            _loadTimeSlots();
            return;
          }
        }

        // Convert backend format to display format and store both
        Map<String, String> slots = {};
        for (String backendTime in timeStrings) {
          try {
            if (backendTime.isNotEmpty) {
              final timeParts = backendTime.split(':');
              if (timeParts.length >= 2) {
                int hour = int.parse(timeParts[0]);
                int minute = int.parse(timeParts[1]);
                String period = hour >= 12 ? 'PM' : 'AM';
                int display12Hour =
                    hour > 12 ? hour - 12 : (hour == 0 ? 12 : hour);
                String displayTime =
                    '${display12Hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')} $period';
                slots[displayTime] = backendTime;
              }
            }
          } catch (e) {
            print('DEBUG: Error parsing time slot: $e');
            continue;
          }
        }

        // Reset retry attempts on success
        _retryAttempts = 0;

        // Ensure we're still mounted before setting state
        if (mounted) {
          setState(() {
            timeSlots = slots;
            selectedDisplayTime = null; // Reset selection when slots change
            isLoading = false;
            errorMessage = null;
          });
        }
      } catch (e) {
        if (mounted) {
          setState(() {
            errorMessage = 'Failed to load time slots. Please try again.';
            isLoading = false;
          });
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (widget.doctorId == null) {
      return const Center(child: Text('Please select a doctor first'));
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
              style: const TextStyle(color: Colors.grey),
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
      children:
          timeSlots.entries.map((entry) {
            final displayTime = entry.key;
            final backendTime = entry.value;
            final isSelected = selectedDisplayTime == displayTime;
            return ChoiceChip(
              label: Text(displayTime),
              selected: isSelected,
              onSelected: (selected) {
                setState(() {
                  selectedDisplayTime = selected ? displayTime : null;
                });
                if (selected) {
                  widget.onTimeSlotSelected(
                    backendTime,
                  ); // Send backend format to parent
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
