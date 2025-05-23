import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:http/http.dart' as http;
import 'package:permission_handler/permission_handler.dart';
import 'package:frontend/Screens/Profile/profile_screen.dart';
import 'package:frontend/constants.dart';

class ConversationalScreen extends StatefulWidget {
  final String token;

  const ConversationalScreen({super.key, required this.token});

  @override
  State<ConversationalScreen> createState() => _ConversationalScreenState();
}

class _ConversationalScreenState extends State<ConversationalScreen> with SingleTickerProviderStateMixin {
  final SpeechToText _speechToText = SpeechToText();
  final FlutterTts _flutterTts = FlutterTts();
  bool _speechEnabled = false;
  bool _isListening = false;
  bool _isSpeaking = false;
  String _lastWords = '';
  bool _isLoading = false;
  String _currentResponse = '';
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _rippleAnimation;
  
  @override
  void initState() {
    super.initState();
    _initSpeech();
    _initTts();
    _requestPermissions();
    _initAnimations();
    
    // Add welcome message
    _currentResponse = "Hello! I'm Dr. Amy, your HealthMate assistant. How can I help you today?";
    _speakResponse(_currentResponse);
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

  Future<void> _requestPermissions() async {
    await Permission.microphone.request();
  }

  Future<void> _initSpeech() async {
    _speechEnabled = await _speechToText.initialize();
    setState(() {});
  }

  Future<void> _initTts() async {
    await _flutterTts.setLanguage("en-US");
    await _flutterTts.setPitch(1.1);
    await _flutterTts.setSpeechRate(0.8);
    await _flutterTts.setVoice({"name": "en-US-Neural2-F", "locale": "en-US"});
  }

  Future<void> _toggleListening() async {
    if (!_speechEnabled) {
      await _initSpeech();
    }

    if (_isListening) {
      await _speechToText.stop();
      if (_lastWords.isNotEmpty) {
        await _getAIResponse(_lastWords);
        _lastWords = '';
      }
    } else {
      await _speechToText.listen(
        onResult: _onSpeechResult,
        listenFor: const Duration(seconds: 30),
        localeId: "en_US",
        cancelOnError: true,
        partialResults: true,
      );
      setState(() {
        _currentResponse = "I'm listening...";
      });
    }
    setState(() {
      _isListening = !_isListening;
    });
  }

  void _onSpeechResult(result) {
    setState(() {
      _lastWords = result.recognizedWords;
      if (_lastWords.isNotEmpty) {
        _currentResponse = "You said: $_lastWords";
      }
    });
  }

  Future<void> _getAIResponse(String message) async {
    setState(() {
      _isLoading = true;
    });

    try {
      final response = await http.post(
        Uri.parse('http://localhost:8000/chat/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${widget.token}',
        },
        body: jsonEncode({'message': message}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final aiResponse = data['response'];
        setState(() {
          _currentResponse = aiResponse;
        });
        await _speakResponse(aiResponse);
      } else {
        setState(() {
          _currentResponse = 'Sorry, I encountered an error. Please try again.';
        });
      }
    } catch (e) {
      setState(() {
        _currentResponse = 'Network error. Please check your connection.';
      });
    } finally {
      setState(() {
        _isLoading = false;
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
  void dispose() {
    _speechToText.stop();
    _flutterTts.stop();
    _animationController.dispose();
    super.dispose();
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
                    if (_isListening || _isSpeaking)
                      AnimatedBuilder(
                        animation: _rippleAnimation,
                        builder: (context, child) {
                          return Transform.scale(
                            scale: _rippleAnimation.value,
                            child: Container(
                              width: 100,
                              height: 100,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: kPrimaryColor.withOpacity(0.2),
                              ),
                            ),
                          );
                        },
                      ),
                    
                    // Main button
                    GestureDetector(
                      onTap: _toggleListening,
                      child: AnimatedBuilder(
                        animation: _scaleAnimation,
                        builder: (context, child) {
                          return Transform.scale(
                            scale: (_isListening || _isSpeaking) ? _scaleAnimation.value : 1.0,
                            child: Container(
                              width: 80,
                              height: 80,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _isListening ? Colors.red : kPrimaryColor,
                                boxShadow: [
                                  BoxShadow(
                                    color: (_isListening ? Colors.red : kPrimaryColor).withOpacity(0.3),
                                    blurRadius: 20,
                                    spreadRadius: 5,
                                  ),
                                ],
                              ),
                              child: Icon(
                                _isListening ? Icons.mic : Icons.mic_none,
                                color: Colors.white,
                                size: 40,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 16),
                
                // Status text
                Text(
                  _isListening ? 'Listening...' : 'Tap to speak',
                  style: TextStyle(
                    color: Colors.black87.withOpacity(0.7),
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ),
          
          // Loading indicator
          if (_isLoading)
            Container(
              color: Colors.black.withOpacity(0.5),
              child: const Center(
                child: CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(kPrimaryColor),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
