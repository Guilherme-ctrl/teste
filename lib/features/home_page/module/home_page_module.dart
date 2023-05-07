import 'package:flutter_modular/flutter_modular.dart';
import 'package:teste_aplication/features/detail_page/detail_page.dart';

import '../home_page.dart';

class HomeModule extends Module {
  @override
  final List<Bind> binds = [];

  @override
  final List<ModularRoute> routes = [
    ChildRoute(
      "${Modular.initialRoute}home/",
      child: (_, __) => const HomePage(),
      transition: TransitionType.noTransition,
    ),
    ChildRoute(
      "${Modular.initialRoute}detail/",
      child: (_, args) => DetailPage(arguments: args.data),
      transition: TransitionType.noTransition,
    ),
  ];
}
