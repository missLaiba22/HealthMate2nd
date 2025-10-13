import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/Screens/Profile/profile_screen.dart';
import 'package:frontend/Screens/Scan_Analysis/scan_analysis_screen.dart';
import 'package:frontend/constants.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:frontend/Screens/Appointments/appointment_screen.dart';
import 'package:frontend/Screens/Appointments/doctor_availability_screen.dart';
import 'package:frontend/Screens/Appointments/my_appointments_screen.dart';
// Removed complex appointment imports - keeping conversational engine simple

class ConversationalScreen extends StatefulWidget {
  final String token;
  final String email;
  final String userRole; // Add user role parameter

  const ConversationalScreen({
    super.key,
    required this.token,
    required this.email,
    required this.userRole,
  });

  @override
  State<ConversationalScreen> createState() => _ConversationalScreenState();
}

class _ConversationalScreenState extends State<ConversationalScreen>
    with TickerProviderStateMixin {
  final _audioRecorder = AudioRecorder();
  final _flutterTts = FlutterTts();
  bool _isRecording = false;
  String _transcribedText = '';
  bool _isProcessing = false;
  bool _isSpeaking = false;
  String _currentResponse = '';
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _rippleAnimation;

  @override
  void initState() {
    super.initState();
    _initRecorder();
    _initAnimations();
    _initTts();

    // Add welcome message
    _currentResponse =
        "Hello! I'm your Medical Assistant. How can I help you today?";
    _speakResponse(_currentResponse);
  }

  Future<void> _initTts() async {
    // Fixed English language for TTS
    await _flutterTts.setLanguage("en-US");
    // Optimized speech parameters for English
    await _flutterTts.setPitch(1.0);
    await _flutterTts.setSpeechRate(0.5);
    await _flutterTts.setVoice({"name": "en-US-language", "locale": "en-US"});
  }

  void _initAnimations() {
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _rippleAnimation = Tween<double>(begin: 1.0, end: 2.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
  }

  Future<void> _initRecorder() async {
    try {
      final hasPermission = await _audioRecorder.hasPermission();
      if (!hasPermission) {
        throw Exception('No permission to record audio');
      }
    } catch (e) {
      print('Error initializing recorder: $e');
    }
  }

  Future<void> _startRecording() async {
    try {
      // Don't start recording if the assistant is speaking
      if (_isSpeaking) {
        return;
      }

      if (await _audioRecorder.hasPermission()) {
        final directory = await getTemporaryDirectory();
        final filePath = '${directory.path}/audio_recording.wav';

        await _audioRecorder.start(
          RecordConfig(encoder: AudioEncoder.wav, sampleRate: 16000),
          path: filePath,
        );

        setState(() {
          _isRecording = true;
        });
      }
    } catch (e) {
      print('Error starting recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    try {
      final path = await _audioRecorder.stop();
      setState(() {
        _isRecording = false;
        _isProcessing = true;
      });

      if (path != null) {
        await _transcribeAudio(path);
      }
    } catch (e) {
      print('Error stopping recording: $e');
      setState(() {
        _isProcessing = false;
      });
    }
  }

  Future<void> _transcribeAudio(String filePath) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('${ApiConfig.baseUrl}/speech/transcribe'),
      );

      // Add Authorization header
      request.headers.addAll({'Authorization': 'Bearer ${widget.token}'});

      request.files.add(
        await http.MultipartFile.fromPath('audio_file', filePath),
      );

      final response = await request.send();
      final responseBody = await response.stream.bytesToString();
      print('Speech transcription response status: ${response.statusCode}');
      print('Speech transcription response body: $responseBody');
      final data = json.decode(responseBody);
      print('Parsed speech data: $data');

      if (response.statusCode == 200 && data['transcription'] != null) {
        // Handle the response more safely - check for nested structure
        String transcribedText;
        if (data['transcription'] is String) {
          transcribedText = data['transcription'];
        } else if (data['transcription'] is Map &&
            data['transcription']['text'] != null) {
          // Handle nested structure: {transcription: {text: "message"}}
          transcribedText = data['transcription']['text'].toString();
        } else {
          transcribedText = data['transcription'].toString();
        }

        if (mounted) {
          setState(() {
            _transcribedText = transcribedText;
            _isProcessing = false;
          });

          if (_transcribedText.isNotEmpty) {
            await _getAIResponse(_transcribedText);
          }
        }
      } else {
        print(
          'Speech transcription failed with status: ${response.statusCode}',
        );
        print('Response body: $responseBody');
        if (mounted) {
          setState(() {
            _transcribedText =
                'Audio processing failed. Please try recording again.';
            _isProcessing = false;
          });
        }
      }
    } catch (e) {
      print('Error transcribing audio: $e');
      if (mounted) {
        setState(() {
          _isProcessing = false;
        });
      }
    }
  }

  Future<void> _getAIResponse(String message) async {
    print('Getting AI response for message: $message');
    setState(() {
      _isProcessing = true;
    });

    try {
      print('Sending chat request to: ${ApiConfig.baseUrl}/chat');
      print('Message: $message');
      print('Token: ${widget.token.substring(0, 20)}...');

      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/chat'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${widget.token}',
        },
        body: jsonEncode({'message': message}),
      );

      print('Chat response status: ${response.statusCode}');
      print('Chat response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('Parsed response data: $data');
        setState(() {
          _currentResponse = data['response'];
        });
        await _speakResponse(data['response']);
      } else {
        print('Chat API error: ${response.statusCode} - ${response.body}');
        setState(() {
          _currentResponse = 'Sorry, I encountered an error. Please try again.';
        });
      }
    } catch (e) {
      print('Error getting AI response: $e');
      setState(() {
        _currentResponse = 'Network error. Please check your connection.';
      });
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }

  // Removed complex appointment booking - keeping conversational engine simple

  Future<void> _speakResponse(String text) async {
    if (text.isNotEmpty) {
      setState(() {
        _isSpeaking = true;
      });
      _animationController.repeat(reverse: true);
      await _flutterTts.speak(text);
      setState(() {
        _isSpeaking = false;
      });
      _animationController.stop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: kPrimaryColor,
        elevation: 0,
        leading: Builder(
          builder:
              (context) => IconButton(
                icon: const Icon(Icons.menu, color: Colors.white),
                onPressed: () {
                  Scaffold.of(context).openDrawer();
                },
              ),
        ),
        title: const Text(
          'Medical Assistant',
          style: TextStyle(color: Colors.white),
        ),
      ),
      drawer: Drawer(
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [kPrimaryColor, Colors.white],
            ),
          ),
          child: ListView(
            padding: EdgeInsets.zero,
            children: [
              DrawerHeader(
                decoration: BoxDecoration(color: kPrimaryColor),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const CircleAvatar(
                      radius: 30,
                      backgroundColor: Colors.white,
                      child: Icon(Icons.person, size: 35, color: kPrimaryColor),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      widget.email,
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                    ),
                  ],
                ),
              ),
              ListTile(
                leading: const Icon(Icons.chat, color: kPrimaryColor),
                title: const Text('Medical Assistant'),
                onTap: () {
                  Navigator.pop(context);
                  setState(() {
                    _currentResponse =
                        "Hello! I'm your Medical Assistant. How can I help you today?";
                    _transcribedText = '';
                    _isProcessing = false;
                    _isSpeaking = false;
                  });
                  _speakResponse(_currentResponse);
                },
              ),
              ListTile(
                leading: const Icon(
                  Icons.medical_services,
                  color: kPrimaryColor,
                ),
                title: const Text('Scan Analysis'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder:
                          (context) => ScanAnalysisScreen(
                            token: widget.token,
                            patientEmail: widget.email,
                          ),
                    ),
                  );
                },
              ),
              ListTile(
                leading: const Icon(Icons.calendar_today, color: kPrimaryColor),
                title: Text(
                  widget.userRole == 'doctor'
                      ? 'My Appointments'
                      : 'Book Appointment',
                ),
                onTap: () {
                  Navigator.pop(context);
                  if (widget.userRole == 'doctor') {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder:
                            (context) => MyAppointmentsScreen(
                              token: widget.token,
                              email: widget.email,
                              userRole: widget.userRole,
                            ),
                      ),
                    );
                  } else {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder:
                            (context) => AppointmentScreen(
                              token: widget.token,
                              email: widget.email,
                            ),
                      ),
                    );
                  }
                },
              ),
              // Only show "Set Availability" for doctors
              if (widget.userRole == 'doctor')
                ListTile(
                  leading: const Icon(Icons.schedule, color: kPrimaryColor),
                  title: const Text('Set Availability'),
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder:
                            (context) => DoctorAvailabilityScreen(
                              token: widget.token,
                              email: widget.email,
                            ),
                      ),
                    );
                  },
                ),
              // Removed complex triage appointment - keeping conversational engine simple
              ListTile(
                leading: const Icon(Icons.person, color: kPrimaryColor),
                title: const Text('Profile Management'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => ProfileScreen(token: widget.token),
                    ),
                  );
                },
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.logout, color: kPrimaryColor),
                title: const Text('Logout'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.pushReplacementNamed(context, '/login');
                },
              ),
            ],
          ),
        ),
      ),
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [kPrimaryColor, Colors.white],
              ),
            ),
          ),

          // Main content
          Column(
            children: [
              // Current response
              Expanded(
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (_currentResponse.isNotEmpty)
                        Column(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 32,
                                vertical: 16,
                              ),
                              child: Text(
                                _currentResponse,
                                style: const TextStyle(
                                  color: Colors.black87,
                                  fontSize: 18,
                                  fontWeight: FontWeight.w400,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                            if (_isSpeaking)
                              const Padding(
                                padding: EdgeInsets.only(top: 8),
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(
                                      Icons.volume_up,
                                      color: kPrimaryColor,
                                      size: 20,
                                    ),
                                    SizedBox(width: 8),
                                    Text(
                                      "Speaking...",
                                      style: TextStyle(
                                        color: kPrimaryColor,
                                        fontSize: 14,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        ),

                      const SizedBox(height: 48),

                      // Voice button section
                      Stack(
                        alignment: Alignment.center,
                        children: [
                          // Ripple effect
                          if (_isRecording)
                            AnimatedBuilder(
                              animation: _rippleAnimation,
                              builder: (context, child) {
                                return Container(
                                  width: 100 * _rippleAnimation.value,
                                  height: 100 * _rippleAnimation.value,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: kPrimaryColor.withOpacity(0.2),
                                  ),
                                );
                              },
                            ),

                          // Record button
                          GestureDetector(
                            onTap:
                                _isRecording ? _stopRecording : _startRecording,
                            child: AnimatedBuilder(
                              animation: _scaleAnimation,
                              builder: (context, child) {
                                return Transform.scale(
                                  scale:
                                      _isRecording
                                          ? _scaleAnimation.value
                                          : 1.0,
                                  child: Container(
                                    width: 80,
                                    height: 80,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      color:
                                          _isRecording
                                              ? Colors.red
                                              : kPrimaryColor,
                                      boxShadow: [
                                        BoxShadow(
                                          color: kPrimaryColor.withOpacity(0.3),
                                          blurRadius: 8,
                                          offset: const Offset(0, 4),
                                        ),
                                      ],
                                    ),
                                    child: Icon(
                                      _isRecording ? Icons.stop : Icons.mic,
                                      color: Colors.white,
                                      size: 32,
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 32),

                      // Status text
                      if (_isProcessing)
                        const Text(
                          'Processing...',
                          style: TextStyle(color: Colors.black54, fontSize: 16),
                        )
                      else if (_isRecording)
                        const Text(
                          'Recording...',
                          style: TextStyle(color: Colors.red, fontSize: 16),
                        ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: kPrimaryColor, size: 24),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(
                color: Colors.black87,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showProfileCompletionDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Complete Your Profile'),
          content: const Text(
            'Would you like to complete your profile now? You can also do this later.',
          ),
          actions: <Widget>[
            TextButton(
              child: const Text('Later'),
              onPressed: () {
                Navigator.pop(context);
              },
            ),
            TextButton(
              child: const Text('Complete Profile'),
              onPressed: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ProfileScreen(token: widget.token),
                  ),
                );
              },
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    _audioRecorder.dispose();
    _flutterTts.stop();
    super.dispose();
  }
}
