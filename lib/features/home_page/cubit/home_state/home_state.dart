import 'package:equatable/equatable.dart';
import 'package:teste_aplication/features/home_page/cubit/presenter/list_presenter.dart';

abstract class HomeState extends Equatable {}

class HomeStateInitial extends HomeState {
  @override
  List<Object?> get props => [];
}

class HomeStateLoading extends HomeState {
  @override
  List<Object?> get props => [];
}

class HomeStateSuccess extends HomeState {
  final List<ListPresenter>? list;

  HomeStateSuccess({required this.list});
  @override
  List<Object?> get props => [list];
}

class HomeStateError extends HomeState {
  final String error;

  HomeStateError({required this.error});
  @override
  List<Object?> get props => [error];
}
