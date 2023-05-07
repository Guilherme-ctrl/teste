import 'package:equatable/equatable.dart';
import 'package:teste_aplication/core/cast/try.dart';

class ListModel extends Equatable {
  final String nome;
  final int regiao;
  final int freq;
  final int rank;
  final String sexo;

  const ListModel(
      {required this.nome,
      required this.regiao,
      required this.freq,
      required this.rank,
      required this.sexo});

  factory ListModel.fromMap(Map<String, dynamic> map) {
    return ListModel(
        nome: tryCast<String>(map['nome'], ""),
        regiao: tryCast<int>(map['regiao'], 0),
        freq: tryCast<int>(map['freq'], 0),
        rank: tryCast<int>(map['rank'], 0),
        sexo: tryCast<String>(map['sexo'], ""));
  }

  static List<ListModel> fromListMap(List maps) =>
      maps.map((e) => ListModel.fromMap(e)).toList();

  @override
  List<Object?> get props => [nome, regiao, freq, rank, sexo];
}
