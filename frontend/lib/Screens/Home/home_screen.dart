import 'package:flutter/material.dart';
import '../../constants.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('HealthMate'),
        backgroundColor: kPrimaryColor,
      ),
      body: const Center(
        child: Text('Welcome to HealthMate'),
      ),
    );
  }
} 