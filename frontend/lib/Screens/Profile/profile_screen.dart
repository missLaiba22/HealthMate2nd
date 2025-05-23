import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ProfileScreen extends StatefulWidget {
  final String token;
  const ProfileScreen({super.key, required this.token});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // Controllers for all fields
  final TextEditingController fullNameController = TextEditingController();
  final TextEditingController dobController = TextEditingController();
  final TextEditingController genderController = TextEditingController();
  final TextEditingController contactController = TextEditingController();
  final TextEditingController medicalConditionsController = TextEditingController();
  final TextEditingController allergiesController = TextEditingController();
  final TextEditingController medicationsController = TextEditingController();
  final TextEditingController emergencyContactController = TextEditingController();
  final TextEditingController licenseController = TextEditingController();
  final TextEditingController specializationController = TextEditingController();
  final TextEditingController experienceController = TextEditingController();

  bool shareHealthData = false;
  bool receiveNotifications = false;
  String role = "patient"; // default
  String? selectedGender; // Add this line to track selected gender

  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    fetchProfile();
  }

  void fetchProfile() async {
    final response = await http.get(
      Uri.parse('http://localhost:8000/profile/'),
      headers: {'Authorization': 'Bearer ${widget.token}'},
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      setState(() {
        fullNameController.text = data['full_name'] ?? '';
        dobController.text = data['date_of_birth'] ?? '';
        // Ensure gender is one of the valid options
        String gender = (data['gender'] ?? '').toString().toLowerCase();
        selectedGender = ['male', 'female', 'other'].contains(gender) ? gender : null;
        genderController.text = selectedGender ?? '';
        contactController.text = data['contact_number'] ?? '';
        role = data['role'] ?? 'patient';
        medicalConditionsController.text = (data['medical_conditions'] ?? []).join(', ');
        allergiesController.text = (data['allergies'] ?? []).join(', ');
        medicationsController.text = (data['medications'] ?? []).join(', ');
        emergencyContactController.text = data['emergency_contact'] ?? '';
        licenseController.text = data['medical_license_number'] ?? '';
        specializationController.text = data['specialization'] ?? '';
        experienceController.text = data['years_of_experience']?.toString() ?? '';
        shareHealthData = data['share_health_data'] ?? false;
        receiveNotifications = data['receive_notifications'] ?? false;
      });
    }
  }

  void saveProfile() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final profile = {
      "full_name": fullNameController.text,
      "date_of_birth": dobController.text,
      "gender": selectedGender,
      "contact_number": contactController.text,
      "role": role,
      "medical_conditions": medicalConditionsController.text.split(',').map((e) => e.trim()).toList(),
      "allergies": allergiesController.text.split(',').map((e) => e.trim()).toList(),
      "medications": medicationsController.text.split(',').map((e) => e.trim()).toList(),
      "emergency_contact": emergencyContactController.text,
      "medical_license_number": licenseController.text,
      "specialization": specializationController.text,
      "years_of_experience": int.tryParse(experienceController.text) ?? 0,
      "share_health_data": shareHealthData,
      "receive_notifications": receiveNotifications,
    };

    final response = await http.put(
      Uri.parse('http://localhost:8000/profile/'),
      headers: {
        'Authorization': 'Bearer ${widget.token}',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(profile),
    );

    if (response.statusCode == 200) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile updated successfully!')),
        );
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update profile: ${response.body}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        backgroundColor: Colors.blue.shade700,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: fullNameController,
                decoration: const InputDecoration(
                  labelText: 'Full Name',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter your full name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: dobController,
                decoration: const InputDecoration(
                  labelText: 'Date of Birth',
                  border: OutlineInputBorder(),
                ),
                readOnly: true,
                onTap: () async {
                  final DateTime? picked = await showDatePicker(
                    context: context,
                    initialDate: DateTime.now(),
                    firstDate: DateTime(1900),
                    lastDate: DateTime.now(),
                  );
                  if (picked != null) {
                    setState(() {
                      dobController.text = "${picked.year}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}";
                    });
                  }
                },
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please select your date of birth';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedGender,
                decoration: const InputDecoration(
                  labelText: 'Gender',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'male', child: Text('Male')),
                  DropdownMenuItem(value: 'female', child: Text('Female')),
                  DropdownMenuItem(value: 'other', child: Text('Other')),
                ],
                onChanged: (String? newValue) {
                  if (newValue != null) {
                    setState(() {
                      selectedGender = newValue;
                      genderController.text = newValue;
                    });
                  }
                },
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please select your gender';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: contactController,
                decoration: const InputDecoration(
                  labelText: 'Contact Number',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.phone,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter your contact number';
                  }
                  if (!RegExp(r'^\+?[\d\s-]{10,}$').hasMatch(value)) {
                    return 'Please enter a valid phone number';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              if (role == 'patient') ...[
                TextFormField(
                  controller: medicalConditionsController,
                  decoration: const InputDecoration(
                    labelText: 'Medical Conditions (comma-separated)',
                    border: OutlineInputBorder(),
                  ),
                  maxLines: 2,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: allergiesController,
                  decoration: const InputDecoration(
                    labelText: 'Allergies (comma-separated)',
                    border: OutlineInputBorder(),
                  ),
                  maxLines: 2,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: medicationsController,
                  decoration: const InputDecoration(
                    labelText: 'Current Medications (comma-separated)',
                    border: OutlineInputBorder(),
                  ),
                  maxLines: 2,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: emergencyContactController,
                  decoration: const InputDecoration(
                    labelText: 'Emergency Contact',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.phone,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter emergency contact number';
                    }
                    if (!RegExp(r'^\+?[\d\s-]{10,}$').hasMatch(value)) {
                      return 'Please enter a valid phone number';
                    }
                    return null;
                  },
                ),
              ],
              if (role == 'doctor') ...[
                TextFormField(
                  controller: licenseController,
                  decoration: const InputDecoration(
                    labelText: 'Medical License Number',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your medical license number';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: specializationController,
                  decoration: const InputDecoration(
                    labelText: 'Specialization',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your specialization';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: experienceController,
                  decoration: const InputDecoration(
                    labelText: 'Years of Experience',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: TextInputType.number,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter years of experience';
                    }
                    if (int.tryParse(value) == null) {
                      return 'Please enter a valid number';
                    }
                    return null;
                  },
                ),
              ],
              const SizedBox(height: 16),
              SwitchListTile(
                title: const Text('Share Health Data'),
                subtitle: const Text('Allow sharing of health data for better care'),
                value: shareHealthData,
                onChanged: (bool value) {
                  setState(() {
                    shareHealthData = value;
                  });
                },
              ),
              SwitchListTile(
                title: const Text('Receive Notifications'),
                subtitle: const Text('Get updates about appointments and health tips'),
                value: receiveNotifications,
                onChanged: (bool value) {
                  setState(() {
                    receiveNotifications = value;
                  });
                },
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: saveProfile,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade700,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Save Profile'),
              ),
            ],
          ),
        ),
      ),
    );
  }
} 