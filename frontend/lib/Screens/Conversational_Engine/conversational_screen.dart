import 'dart:io';
import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:frontend/Screens/Profile/profile_screen.dart';
import 'package:frontend/constants.dart';
import 'package:flutter_tts/flutter_tts.dart';

class ConversationalScreen extends StatefulWidget {
  final String token;
  final String email;

  const ConversationalScreen({super.key, required this.token, required this.email});

  @override
  State<ConversationalScreen> createState() => _ConversationalScreenState();
}

class _ConversationalScreenState extends State<ConversationalScreen> with TickerProviderStateMixin {
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
    _currentResponse = "Hello! I'm Dr. Amy, your HealthMate assistant. How can I help you today?";
    _speakResponse(_currentResponse);
  }

  Future<void> _initTts() async {
    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setPitch(1.0);
    await _flutterTts.setSpeechRate(0.5);
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
      if (await _audioRecorder.hasPermission()) {
        final directory = await getTemporaryDirectory();
        final filePath = '${directory.path}/audio_recording.wav';
        
        await _audioRecorder.start(
          RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
          ),
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
        Uri.parse('http://192.168.18.60:8000/speech/transcribe'),
      );

      request.files.add(
        await http.MultipartFile.fromPath(
          'audio_file',
          filePath,
        ),
      );

      final response = await request.send();
      final responseBody = await response.stream.bytesToString();
      final data = json.decode(responseBody);

      setState(() {
        _transcribedText = data['text'];
        _isProcessing = false;
      });

      if (_transcribedText.isNotEmpty) {
        await _getAIResponse(_transcribedText);
      }
    } catch (e) {
      print('Error transcribing audio: $e');
      setState(() {
        _isProcessing = false;
      });
    }
  }

  Future<void> _getAIResponse(String message) async {
    setState(() {
      _isProcessing = true;
    });

    try {
      final response = await http.post(
        Uri.parse('http://192.168.18.60:8000/chat'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${widget.token}',
        },
        body: jsonEncode({
          'message': message,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _currentResponse = data['response'];
        });
        await _speakResponse(data['response']);
      } else {
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
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.account_circle, color: Colors.white),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => ProfileScreen(token: widget.token)),
              );
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  kPrimaryColor,
                  Colors.white,
                ],
              ),
            ),
          ),
          
          // Main content
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Current response
                if (_currentResponse.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
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
                      onTap: _isRecording ? _stopRecording : _startRecording,
                      child: AnimatedBuilder(
                        animation: _scaleAnimation,
                        builder: (context, child) {
                          return Transform.scale(
                            scale: _isRecording ? _scaleAnimation.value : 1.0,
                            child: Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _isRecording ? Colors.red : kPrimaryColor,
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
                    style: TextStyle(
                      color: Colors.black54,
                      fontSize: 16,
                    ),
                  )
                else if (_isRecording)
                  const Text(
                    'Recording...',
                    style: TextStyle(
                      color: Colors.red,
                      fontSize: 16,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
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
