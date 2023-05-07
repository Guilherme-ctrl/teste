import '../models/list_model.dart';

abstract class IListDatasource {
  Future<List<ListModel>> getList();
}
