import 'package:teste_aplication/core/domain/entities/list_entity.dart';
import 'package:teste_aplication/features/home_page/cubit/presenter/list_presenter.dart';

extension ListListPresenterMapper on List<ListEntity> {
  List<ListPresenter> toPresenterList() => map((e) => e.toPresenter()).toList();
}

extension ListEntiyMapper on ListEntity {
  ListPresenter toPresenter() => ListPresenter(
      nome: nome, regiao: regiao, freq: freq, rank: rank, sexo: sexo);
}
