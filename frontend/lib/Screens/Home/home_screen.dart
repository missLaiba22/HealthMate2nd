import 'package:flutter/material.dart';
import 'package:frontend/Screens/Conversational_Engine/conversational_screen.dart';
import 'package:frontend/Screens/Scan_Analysis/scan_analysis_screen.dart';
import 'package:frontend/Screens/Profile/profile_screen.dart';
import 'package:frontend/constants.dart';

class HomeScreen extends StatefulWidget {
  final String token;
  final String email;

  const HomeScreen({
    Key? key,
    required this.token,
    required this.email,
  }) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [];

  @override
  void initState() {
    super.initState();
    _screens.addAll([
      ConversationalScreen(token: widget.token, email: widget.email),
      ScanAnalysisScreen(token: widget.token),
      ProfileScreen(token: widget.token),
    ]);
  }

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(
            icon: Icon(Icons.chat),
            label: 'Chat',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.medical_services),
            label: 'Scan',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: kPrimaryColor,
        unselectedItemColor: Colors.grey,
        onTap: _onItemTapped,
      ),
    );
  }
} 