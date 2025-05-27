import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/Screens/Appointments/components/appointment_card.dart';
import 'package:frontend/Screens/Appointments/components/doctor_availability_card.dart';
import 'package:frontend/Screens/Appointments/components/time_slot_selector.dart';
import 'package:frontend/services/appointment_service.dart';

class AppointmentScreen extends StatefulWidget {
  final String token;
  final String email;

  const AppointmentScreen({
    Key? key,
    required this.token,
    required this.email,
  }) : super(key: key);

  @override
  State<AppointmentScreen> createState() => _AppointmentScreenState();
}

class _AppointmentScreenState extends State<AppointmentScreen> with SingleTickerProviderStateMixin {
  DateTime selectedDate = DateTime.now();
  String? selectedDoctor;
  String? selectedTimeSlot;
  bool isLoading = false;
  String? errorMessage;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Schedule Appointment'),
        backgroundColor: kPrimaryColor,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          tabs: const [
            Tab(text: 'Select Doctor'),
            Tab(text: 'Choose Date'),
            Tab(text: 'Pick Time'),
          ],
        ),
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        errorMessage!,
                        style: const TextStyle(color: Colors.red),
                      ),
                      ElevatedButton(
                        onPressed: () {
                          setState(() {
                            errorMessage = null;
                          });
                        },
                        child: const Text('Try Again'),
                      ),
                    ],
                  ),
                )
              : TabBarView(
                  controller: _tabController,
                  children: [
                    // Doctor Selection Tab
                    Padding(
                      padding: const EdgeInsets.all(defaultPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Available Doctors',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: defaultPadding),
                          Expanded(
                            child: DoctorAvailabilityCard(
                              onDoctorSelected: (doctor) {
                                setState(() {
                                  selectedDoctor = doctor;
                                });
                                _tabController.animateTo(1);
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Date Selection Tab
                    Padding(
                      padding: const EdgeInsets.all(defaultPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Select Date',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: defaultPadding),
                          Expanded(
                            child: CalendarDatePicker(
                              initialDate: selectedDate,
                              firstDate: DateTime.now(),
                              lastDate: DateTime.now().add(const Duration(days: 30)),
                              onDateChanged: (date) {
                                setState(() {
                                  selectedDate = date;
                                });
                                _tabController.animateTo(2);
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Time Slot Selection Tab
                    Padding(
                      padding: const EdgeInsets.all(defaultPadding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Available Time Slots',
                            style: TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: defaultPadding),
                          Expanded(
                            child: TimeSlotSelector(
                              selectedDate: selectedDate,
                              doctorId: selectedDoctor,
                              onTimeSlotSelected: (timeSlot) {
                                setState(() {
                                  selectedTimeSlot = timeSlot;
                                });
                              },
                            ),
                          ),
                          const SizedBox(height: defaultPadding),
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton(
                              onPressed: _canBookAppointment()
                                  ? () => _bookAppointment()
                                  : null,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: kPrimaryColor,
                                padding: const EdgeInsets.symmetric(vertical: 16),
                              ),
                              child: const Text(
                                'Book Appointment',
                                style: TextStyle(fontSize: 16),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
    );
  }

  bool _canBookAppointment() {
    return selectedDoctor != null && selectedTimeSlot != null;
  }

  Future<void> _bookAppointment() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final appointmentService = AppointmentService(widget.token);
      await appointmentService.bookAppointment(
        doctorId: selectedDoctor!,
        date: selectedDate,
        timeSlot: selectedTimeSlot!,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Appointment booked successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Failed to book appointment. Please try again.';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }
} 