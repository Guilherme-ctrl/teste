import 'package:equatable/equatable.dart';

class ListEntity extends Equatable {
  final String nome;
  final int regiao;
  final int freq;
  final int rank;
  final String sexo;

  const ListEntity(
      {required this.nome,
      required this.regiao,
      required this.freq,
      required this.rank,
      required this.sexo});

  @override
  List<Object?> get props => [nome, regiao, freq, rank, sexo];
}
