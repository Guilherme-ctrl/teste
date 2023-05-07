import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_modular/flutter_modular.dart';
import 'package:teste_aplication/features/app/module/app_module.dart';
import 'package:teste_aplication/features/app/presentation/app_widget.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(ModularApp(
      debugMode: kDebugMode, module: AppModule(), child: const AppWidget()));
}
