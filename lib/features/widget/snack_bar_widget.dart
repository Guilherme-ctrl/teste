import 'package:flutter/material.dart';

class SnackBarWidget {
  SnackBarWidget(
    BuildContext context, {
    required String message,
    Color? color,
    Key? key,
  }) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: color ?? Colors.red,
        content: Text(
          message,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 15,
          ),
        ),
      ),
    );
  }
}
