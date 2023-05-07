import 'package:dartz/dartz.dart';
import 'package:teste_aplication/core/data/datasources/list_datasource.dart';
import 'package:teste_aplication/core/domain/entities/list_entity.dart';
import 'package:teste_aplication/core/domain/mapper/list_model_mapper.dart';
import 'package:teste_aplication/core/domain/repositories/list_repositories.dart';
import 'package:teste_aplication/core/errors/failure.dart';

class ListRepositotyImplementation implements IListRepository {
  final IListDatasource datasource;

  ListRepositotyImplementation(this.datasource);

  @override
  Future<Either<Failure, List<ListEntity>>> getList() async {
    try {
      final result = await datasource.getList();
      return Right(result.toEntityList());
    } catch (e) {
      return Left(DataFailure());
    }
  }
}
