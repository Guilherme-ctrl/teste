import 'package:flutter/material.dart';
import 'package:flutter_modular/flutter_modular.dart';

class EmptyPage extends StatefulWidget {
  const EmptyPage({super.key});

  @override
  State<EmptyPage> createState() => _EmptyPageState();
}

class _EmptyPageState extends State<EmptyPage> {
  @override
  void initState() {
    super.initState();
    _initializeScreen();
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
          child: Text(
        "Ranking",
        style: TextStyle(fontSize: 32),
      )),
    );
  }

  Future<void> _initializeScreen() async {
    await Future.delayed(const Duration(seconds: 2));
    Modular.to.pushReplacementNamed('/initial/home/');
  }
}
