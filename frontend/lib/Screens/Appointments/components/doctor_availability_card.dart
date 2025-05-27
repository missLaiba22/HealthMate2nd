import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/services/appointment_service.dart';

class DoctorAvailabilityCard extends StatefulWidget {
  final Function(String) onDoctorSelected;

  const DoctorAvailabilityCard({
    Key? key,
    required this.onDoctorSelected,
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
      // TODO: Replace with actual API call
      // Simulated data for now
      await Future.delayed(const Duration(seconds: 1));
      setState(() {
        doctors = [
          {
            'id': '1',
            'name': 'Dr. Sarah Johnson',
            'specialization': 'General Physician',
            'rating': 4.8,
            'experience': '10 years',
          },
          {
            'id': '2',
            'name': 'Dr. Michael Chen',
            'specialization': 'Cardiologist',
            'rating': 4.9,
            'experience': '15 years',
          },
          {
            'id': '3',
            'name': 'Dr. Emily Brown',
            'specialization': 'Pediatrician',
            'rating': 4.7,
            'experience': '8 years',
          },
        ];
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
            ElevatedButton(
              onPressed: _loadDoctors,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    return Column(
      children: doctors.map((doctor) {
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
                          style: const TextStyle(
                            color: Colors.grey,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(Icons.star, color: Colors.amber, size: 16),
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
                              style: const TextStyle(
                                color: Colors.grey,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  if (isSelected)
                    const Icon(
                      Icons.check_circle,
                      color: kPrimaryColor,
                    ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
} 