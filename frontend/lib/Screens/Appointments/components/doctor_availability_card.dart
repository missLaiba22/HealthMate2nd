import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';

class DoctorAvailabilityCard extends StatefulWidget {
  final Function(String) onDoctorSelected;
  final String token;

  const DoctorAvailabilityCard({
    Key? key,
    required this.onDoctorSelected,
    required this.token,
  }) : super(key: key);

  @override
  State<DoctorAvailabilityCard> createState() => _DoctorAvailabilityCardState();
}

class _DoctorAvailabilityCardState extends State<DoctorAvailabilityCard> {
  bool isLoading = false;
  List<Map<String, dynamic>> doctors = [];
  String? selectedDoctorId;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    _loadDoctors();
  }

  Future<void> _loadDoctors() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    try {
      final appointmentService = AppointmentService(widget.token);
      final doctorsData = await appointmentService.getDoctors();

      setState(() {
        doctors =
            doctorsData.map((doctor) {
              return {
                'id': doctor['email'], // Use email as ID
                'name': doctor['full_name'] ?? 'Dr. Unknown',
                'specialization':
                    doctor['specialization'] ?? 'General Medicine',
                'rating':
                    4.5, // Default rating since we don't have this in the database yet
                'experience': '${doctor['years_of_experience'] ?? 0} years',
                'email': doctor['email'],
                'contact_number': doctor['contact_number'] ?? '',
                'medical_license_number':
                    doctor['medical_license_number'] ?? '',
              };
            }).toList();
      });
    } catch (e) {
      setState(() {
        errorMessage = 'Failed to load doctors. Please try again.';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (errorMessage != null) {
      return Center(
        child: Column(
          children: [
            Text(errorMessage!, style: const TextStyle(color: Colors.red)),
            ElevatedButton(onPressed: _loadDoctors, child: const Text('Retry')),
          ],
        ),
      );
    }

    if (doctors.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.person_off, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'No doctors available',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey,
                fontWeight: FontWeight.w500,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Please try again later',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: doctors.length,
      itemBuilder: (context, index) {
        final doctor = doctors[index];
        final isSelected = selectedDoctorId == doctor['id'];
        return Card(
          margin: const EdgeInsets.only(bottom: defaultPadding),
          child: InkWell(
            onTap: () {
              setState(() {
                selectedDoctorId = doctor['id'];
              });
              widget.onDoctorSelected(doctor['id']);
            },
            child: Container(
              padding: const EdgeInsets.all(defaultPadding),
              decoration: BoxDecoration(
                border: Border.all(
                  color: isSelected ? kPrimaryColor : Colors.transparent,
                  width: 2,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  const CircleAvatar(
                    radius: 30,
                    backgroundColor: kPrimaryLightColor,
                    child: Icon(Icons.person, color: kPrimaryColor, size: 30),
                  ),
                  const SizedBox(width: defaultPadding),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          doctor['name'],
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          doctor['specialization'],
                          style: const TextStyle(color: Colors.grey),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(
                              Icons.star,
                              color: Colors.amber,
                              size: 16,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              doctor['rating'].toString(),
                              style: const TextStyle(
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            const SizedBox(width: 16),
                            Text(
                              '${doctor['experience']} experience',
                              style: const TextStyle(color: Colors.grey),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  if (isSelected)
                    const Icon(Icons.check_circle, color: kPrimaryColor),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
