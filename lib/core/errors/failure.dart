import 'package:equatable/equatable.dart';

abstract class Failure extends Equatable {}

class DataFailure extends Failure {
  final String message;

  DataFailure({this.message = "Ocorreu um erro, tente novamente"});

  @override
  List<Object?> get props => [];
}
