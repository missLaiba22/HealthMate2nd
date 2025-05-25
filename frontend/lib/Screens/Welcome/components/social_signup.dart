import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../../constants.dart';
import 'social_icon.dart';

class SocialSignUp extends StatelessWidget {
  const SocialSignUp({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        SocialIcon(
          iconSrc: "assets/icons/facebook.svg",
          press: () {
            // TODO: Implement Facebook signup
          },
        ),
        SocialIcon(
          iconSrc: "assets/icons/google-plus.svg",
          press: () {
            // TODO: Implement Google signup
          },
        ),
        SocialIcon(
          iconSrc: "assets/icons/twitter.svg",
          press: () {
            // TODO: Implement Twitter signup
          },
        ),
      ],
    );
  }
} 