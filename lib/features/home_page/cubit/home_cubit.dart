import 'package:bloc/bloc.dart';
import 'package:teste_aplication/core/domain/repositories/list_repositories.dart';
import 'package:teste_aplication/core/errors/failure.dart';
import 'package:teste_aplication/features/home_page/cubit/home_state/home_state.dart';
import 'package:teste_aplication/features/home_page/cubit/presenter/list_presenter.dart';
import 'package:teste_aplication/features/home_page/cubit/presenter/mapper/list_mapper.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class HomeCubit extends Cubit<HomeState> {
  final IListRepository _repository;
  List<ListPresenter> list = [];

  HomeCubit(this._repository) : super(HomeStateInitial());

  Future<void> getList() async {
    emit(HomeStateLoading());
    final result = await _repository.getList();
    final state = result.fold(
        (error) => HomeStateError(
            error: error is DataFailure
                ? error.message
                : "Ocorreu um erro, tente novamente."), (entity) {
      list = entity.toPresenterList();
      return HomeStateSuccess(list: entity.toPresenterList());
    });
    emit(state);
  }
}
