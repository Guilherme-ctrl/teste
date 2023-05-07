import 'package:teste_aplication/core/data/models/list_model.dart';
import 'package:teste_aplication/core/domain/entities/list_entity.dart';

extension ListListModelMapper on List<ListModel> {
  List<ListEntity> toEntityList() => map((e) => e.toEntity()).toList();
}

extension ListModelMapper on ListModel {
  ListEntity toEntity() => ListEntity(
      nome: nome, regiao: regiao, freq: freq, rank: rank, sexo: sexo);
}
