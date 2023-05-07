import 'package:flutter/material.dart';

class LoadingScreenWidget extends StatelessWidget {
  final String? message;

  const LoadingScreenWidget({this.message, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black.withOpacity(0.6),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(
                Colors.purple,
              ),
            ),
            if (message != null)
              Padding(
                padding: const EdgeInsets.only(top: 12.0),
                child: Text(
                  message!,
                  style: const TextStyle(
                    color: Colors.white,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
