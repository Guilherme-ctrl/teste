import 'package:dio/dio.dart';
import 'package:flutter_modular/flutter_modular.dart';
import 'package:teste_aplication/core/data/repositories/list_repositories_implementation.dart';
import 'package:teste_aplication/features/empty_page/empty_page.dart';
import 'package:teste_aplication/features/home_page/module/home_page_module.dart';

import '../../../core/data/datasources/list_datasource_implementation.dart';
import '../../home_page/cubit/home_cubit.dart';

class AppModule extends Module {
  @override
  final List<Bind> binds = [
    Bind((i) => Dio()),
    Bind((i) => ListDatasourceImplementation(i.get())),
    Bind((i) => ListRepositotyImplementation(i.get())),
    Bind((i) => HomeCubit(i.get())),
  ];

  @override
  final List<ModularRoute> routes = [
    ChildRoute(
      Modular.initialRoute,
      child: (_, __) => const EmptyPage(),
      transition: TransitionType.noTransition,
    ),
    ModuleRoute(
      "${Modular.initialRoute}initial/",
      module: HomeModule(),
      transition: TransitionType.noTransition,
    ),
  ];
}
