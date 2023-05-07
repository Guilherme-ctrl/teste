import 'package:dio/dio.dart';
import 'package:teste_aplication/core/data/datasources/list_datasource.dart';
import 'package:teste_aplication/core/data/models/list_model.dart';

class ListDatasourceImplementation implements IListDatasource {
  final Dio dio;

  ListDatasourceImplementation(this.dio);

  @override
  Future<List<ListModel>> getList() async {
    try {
      const url = "https://servicodados.ibge.gov.br/api/v2/censos/nomes/";
      final response = await dio.get(url);
      return ListModel.fromListMap(response.data);
    } catch (e) {
      rethrow;
    }
  }
}
