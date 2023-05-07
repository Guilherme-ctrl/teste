import 'package:dartz/dartz.dart';
import 'package:teste_aplication/core/errors/failure.dart';

import '../entities/list_entity.dart';

abstract class IListRepository {
  Future<Either<Failure, List<ListEntity>>> getList();
}
