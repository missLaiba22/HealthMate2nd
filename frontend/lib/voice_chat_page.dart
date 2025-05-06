import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:logging/logging.dart';
import 'package:web_socket_channel/io.dart';
import 'package:flutter/foundation.dart';

class VoiceChatPage extends StatefulWidget {
  const VoiceChatPage({super.key});

  @override
  State<VoiceChatPage> createState() => _VoiceChatPageState();
}

class _VoiceChatPageState extends State<VoiceChatPage> {
  final Logger _logger = Logger('VoiceChatPage');
  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
  final FlutterSoundPlayer _player = FlutterSoundPlayer();
  bool isRecorderInitialized = false;
  bool isPlayerInitialized = false;
  bool _isRecording = false;
  final audioStreamController = StreamController<Uint8List>.broadcast();

  IOWebSocketChannel? _webSocketChannel;
  bool _isConnecting = false;
  Timer? _reconnectTimer;

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  @override
  void dispose() {
    _recorder.closeRecorder();
    _player.closePlayer();
    audioStreamController.close();
    _webSocketChannel?.sink.close();
    _reconnectTimer?.cancel();
    super.dispose();
  }

  Future<void> _initialize() async {
    await _initRecorderInIsolate();
    await _initPlayerInIsolate();
    await _connectWebSocket();
  }

  Future<void> _initRecorderInIsolate() async {
    try {
      await compute(_initRecorderIsolate, _recorder);
      if (mounted) {
        setState(() => isRecorderInitialized = true);
        _logger.info('Recorder initialized');
      }
    } catch (e) {
      _logger.severe('Recorder initialization failed: $e');
    }
  }

  static Future<void> _initRecorderIsolate(
    FlutterSoundRecorder recorder,
  ) async {
    var status = await Permission.microphone.request();
    if (status != PermissionStatus.granted) {
      throw Exception('Microphone permission denied');
    }
    await recorder.openRecorder();
    await recorder.setSubscriptionDuration(const Duration(milliseconds: 200));
  }

  Future<void> _initPlayerInIsolate() async {
    try {
      await compute(_initPlayerIsolate, _player);
      if (mounted) {
        setState(() => isPlayerInitialized = true);
        _logger.info('Player initialized');
      }
    } catch (e) {
      _logger.severe('Player initialization failed: $e');
    }
  }

  static Future<void> _initPlayerIsolate(FlutterSoundPlayer player) async {
    await player.openPlayer();
  }

  Future<void> _connectWebSocket() async {
    if (_isConnecting) return;
    _isConnecting = true;

    try {
      _webSocketChannel = IOWebSocketChannel.connect(
        Uri.parse('ws://192.168.18.60:8000/ws/voice-chat'),
        pingInterval: const Duration(seconds: 10),
      );
      _logger.info('WebSocket connected');

      _webSocketChannel!.stream.listen(
        (data) {
          if (data is Uint8List) {
            _handleIncomingAudio(data);
          } else {
            _logger.warning('Received unknown data type: ${data.runtimeType}');
          }
        },
        onDone: () {
          _logger.warning('WebSocket closed. Reconnecting...');
          _scheduleReconnect();
        },
        onError: (error) {
          _logger.severe('WebSocket error: $error');
          _scheduleReconnect();
        },
      );
    } catch (e) {
      _logger.severe('WebSocket connection failed: $e');
      _scheduleReconnect();
    } finally {
      _isConnecting = false;
    }
  }

  void _scheduleReconnect() {
    if (_reconnectTimer != null && _reconnectTimer!.isActive) return;

    _reconnectTimer = Timer(const Duration(seconds: 5), () {
      _connectWebSocket();
    });
  }

  Future<void> _handleIncomingAudio(Uint8List data) async {
    if (!isPlayerInitialized) {
      _logger.warning('Player not initialized');
      return;
    }

    try {
      await _player.startPlayer(
        fromDataBuffer: data,
        codec: Codec.pcm16,
        sampleRate: 16000,
        numChannels: 1,
      );
      _logger.info('Playing AI response');
    } catch (e) {
      _logger.severe('Audio playback error: $e');
    }
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      await _recorder.stopRecorder();
      if (mounted) {
        setState(() => _isRecording = false);
      }
      _logger.info('Recording stopped');
    } else {
      if (!isRecorderInitialized) {
        _logger.warning('Recorder not initialized');
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(const SnackBar(content: Text('Recorder not ready')));
        }
        return;
      }
      if (_webSocketChannel == null) {
        _logger.warning('WebSocket not connected');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('WebSocket not connected')),
          );
        }
        await _connectWebSocket();
        return;
      }

      try {
        await _recorder.startRecorder(
          toStream: audioStreamController.sink,
          codec: Codec.pcm16,
          sampleRate: 16000,
          numChannels: 1,
          audioSource: AudioSource.microphone,
        );

        audioStreamController.stream.listen(
          (data) {
            // 🔍 Detect if a WAV header is accidentally included
            if (data.length >= 4 &&
                String.fromCharCodes(data.sublist(0, 4)) == "RIFF") {
              _logger.warning("⚠️ WAV header detected! Audio is not raw PCM.");
            }
            _logger.info('Sending audio chunk: ${data.length} bytes');
            _webSocketChannel?.sink.add(data);
          },
          onError: (error) {
            _logger.severe('Audio stream error: $error');
          },
        );

        if (mounted) {
          setState(() => _isRecording = true);
        }
        _logger.info('Recording started');
      } catch (e) {
        _logger.severe('Recording error: $e');
        if (mounted) {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text('Recording failed: $e')));
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('HealthMate Voice Chat')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton.icon(
              onPressed: _toggleRecording,
              icon: Icon(_isRecording ? Icons.stop : Icons.mic),
              label: Text(_isRecording ? 'Stop Recording' : 'Start Talking'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
                backgroundColor: _isRecording ? Colors.red : Colors.blue,
                foregroundColor: Colors.white,
              ),
            ),
            const SizedBox(height: 20),
            if (_isRecording)
              const Column(
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 8),
                  Text('Recording in progress...'),
                ],
              ),
          ],
        ),
      ),
    );
  }
}
