import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_modular/flutter_modular.dart';
import 'package:teste_aplication/features/detail_page/arguments/detail_page_arguments.dart';
import 'package:teste_aplication/features/home_page/cubit/home_cubit.dart';
import 'package:teste_aplication/features/home_page/cubit/home_state/home_state.dart';
import 'package:teste_aplication/features/home_page/cubit/presenter/list_presenter.dart';
import 'package:teste_aplication/features/home_page/widgets/card_widget.dart';

import '../widget/loading_screen_widget.dart';
import '../widget/snack_bar_widget.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _cubit = Modular.get<HomeCubit>();
  bool loading = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _cubit.getList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.blue,
      appBar: AppBar(
        title: const Text("Ranking"),
        centerTitle: true,
        elevation: 0,
      ),
      body: BlocConsumer(
        listener: _listener,
        bloc: _cubit,
        builder: (context, state) {
          if (_cubit.list.isNotEmpty) {
            return _onState(_cubit.list);
          }
          return const SizedBox();
        },
      ),
    );
  }

  Widget _onState(List<ListPresenter> list) {
    double height = MediaQuery.of(context).size.height;
    double width = MediaQuery.of(context).size.width;
    list.sort((a, b) => a.rank.compareTo(b.rank));

    List<String> nome = list.map((e) => e.nome).toList();

    List<int> rank = list.map((e) => e.rank).toList();
    List<int> freq = list.map((e) => e.freq).toList();
    List<String> sexo = list.map((e) => e.sexo).toList();
    List<int> regiao = list.map((e) => e.regiao).toList();

    return Column(
      children: [
        Container(
            height: height * .2,
            width: width,
            color: Colors.blue,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    _rank(nome[2], 80, 60, "3º", Colors.green, () {
                      Modular.to.pushNamed('/initial/detail/',
                          arguments: DetailPageArguments(
                              nome: nome[2],
                              regiao: regiao[2],
                              freq: freq[2],
                              rank: rank[2],
                              sexo: sexo[2]));
                    }),
                    const SizedBox(width: 40),
                    _rank(nome[0], 130, 60, "1º", Colors.orange, () {
                      Modular.to.pushNamed('/initial/detail/',
                          arguments: DetailPageArguments(
                              nome: nome[0],
                              regiao: regiao[0],
                              freq: freq[0],
                              rank: rank[0],
                              sexo: sexo[0]));
                    }),
                    const SizedBox(width: 40),
                    _rank(nome[1], 100, 60, "2º", Colors.yellow, () {
                      Modular.to.pushNamed('/initial/detail/',
                          arguments: DetailPageArguments(
                              nome: nome[1],
                              regiao: regiao[1],
                              freq: freq[1],
                              rank: rank[1],
                              sexo: sexo[1]));
                    })
                  ],
                )
              ],
            )),
        Expanded(
          child: Container(
            decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(40),
                    topRight: Radius.circular(40))),
            child: Padding(
              padding: const EdgeInsets.only(top: 32.0),
              child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: list.length - 3,
                  itemBuilder: (context, index) {
                    return Column(
                      children: [
                        InkWell(
                          onTap: () {
                            Modular.to.pushNamed('/initial/detail/',
                                arguments: DetailPageArguments(
                                    nome: nome
                                        .getRange(3, nome.length)
                                        .toList()[index],
                                    regiao: regiao
                                        .getRange(3, regiao.length)
                                        .toList()[index],
                                    freq: freq
                                        .getRange(3, freq.length)
                                        .toList()[index],
                                    rank: rank
                                        .getRange(3, rank.length)
                                        .toList()[index],
                                    sexo: sexo
                                        .getRange(3, sexo.length)
                                        .toList()[index]));
                          },
                          child: CardWidget(
                            nome: nome.getRange(3, nome.length).toList()[index],
                            rank: rank.getRange(3, rank.length).toList()[index],
                            freq: freq.getRange(3, freq.length).toList()[index],
                          ),
                        ),
                        const SizedBox(height: 10),
                        Visibility(
                          visible: index == list.length - 4 ? false : true,
                          child: const Divider(
                            color: Colors.lightBlueAccent,
                            thickness: 1,
                            indent: 70,
                            endIndent: 32,
                          ),
                        )
                      ],
                    );
                  }),
            ),
          ),
        ),
      ],
    );
  }

  Widget _rank(String nome, double height, double width, String rank,
      Color color, VoidCallback onPressed) {
    return Column(
      children: [
        Text(
          nome,
          style: const TextStyle(
              color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
        ),
        InkWell(
          onTap: onPressed,
          child: Container(
            color: color,
            height: height,
            width: width,
            child: Center(
              child: Text(
                rank,
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 36,
                    fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _listener(context, state) {
    _closeIfLoading();

    if (state is HomeStateError) {
      showFailureMessage(state.error);
    } else if (state is! HomeStateSuccess) {
      loading = true;
      showDialog(
          context: context,
          useRootNavigator: false,
          builder: (_) => const LoadingScreenWidget(
                message: 'Carregando...',
              ));
    }
  }

  void showFailureMessage(String message) {
    Modular.to.pop();
    SnackBarWidget(context, message: message);
  }

  void _closeIfLoading() {
    if (loading) {
      Modular.to.pop();
      loading = false;
    }
  }
}
