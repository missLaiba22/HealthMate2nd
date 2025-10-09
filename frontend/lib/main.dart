// ignore_for_file: depend_on_referenced_packages

import 'package:flutter/material.dart';
import 'package:frontend/constants.dart';
import 'package:frontend/Screens/Welcome/welcome_screen.dart'; // Your existing welcome screen
import 'package:frontend/Screens/Login/login_screen.dart'; // Make sure this exists
import 'package:frontend/Screens/Signup/signup_screen.dart'; // Make sure this exists
import 'package:frontend/Screens/Scan_Analysis/scan_analysis_screen.dart'; // Make sure this exists
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(const HealthMateApp());
}

class HealthMateApp extends StatelessWidget {
  const HealthMateApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HealthMate',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primaryColor: kPrimaryColor,
        scaffoldBackgroundColor: Colors.white,
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            elevation: 0,
            foregroundColor: Colors.white,
            backgroundColor: kPrimaryColor,
            shape: const StadiumBorder(),
            maximumSize: const Size(double.infinity, 56),
            minimumSize: const Size(double.infinity, 56),
          ),
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: kPrimaryLightColor,
          iconColor: kPrimaryColor,
          prefixIconColor: kPrimaryColor,
          contentPadding: EdgeInsets.symmetric(
            horizontal: defaultPadding,
            vertical: defaultPadding,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(30)),
            borderSide: BorderSide.none,
          ),
        ),
      ),
      home:
          const WelcomeScreen(), // Your starting screen (can navigate to login/signup)
      routes: {
        '/login': (context) => const LoginScreen(),
        '/signup': (context) => const SignUpScreen(),
        '/scan': (context) => FutureBuilder<Map<String, String?>>(
          future: SharedPreferences.getInstance().then((prefs) => {
            'token': prefs.getString('token'),
            'email': prefs.getString('email'),
          }),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(
                  child: CircularProgressIndicator(),
                ),
              );
            }
            
            final data = snapshot.data;
            final token = data?['token'];
            final email = data?['email'];
            
            if (token == null) {
              return const LoginScreen();
            }
            
            return ScanAnalysisScreen(
              token: token,
              patientEmail: email,
            );
          },
        ),
        // You can add more routes as needed
      },
    );
  }
}
