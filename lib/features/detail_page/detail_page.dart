import 'package:flutter/material.dart';
import 'package:teste_aplication/features/detail_page/arguments/detail_page_arguments.dart';

class DetailPage extends StatefulWidget {
  final DetailPageArguments arguments;
  const DetailPage({super.key, required this.arguments});

  @override
  State<DetailPage> createState() => _DetailPageState();
}

class _DetailPageState extends State<DetailPage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Detalhes"),
        centerTitle: true,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.only(top: 32.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            Align(
              alignment: Alignment.topCenter,
              child: CircleAvatar(
                radius: 40,
                child: Text(
                  widget.arguments.nome.substring(0, 1),
                  style: const TextStyle(fontSize: 32),
                ),
              ),
            ),
            const SizedBox(height: 18),
            const Divider(
              thickness: 1,
              color: Colors.blue,
              indent: 30,
              endIndent: 30,
            ),
            const SizedBox(height: 18),
            SizedBox(
              height: 30,
              width: MediaQuery.of(context).size.width,
              child: Center(
                  child: Text(
                "${widget.arguments.nome}:  ${widget.arguments.rank}º",
                style: const TextStyle(fontSize: 21),
              )),
            ),
            const SizedBox(height: 18),
            SizedBox(
              height: 30,
              width: MediaQuery.of(context).size.width,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    "Região:  ${widget.arguments.regiao}",
                    style: const TextStyle(fontSize: 16),
                  ),
                  const SizedBox(width: 30),
                  Text(
                    "Frequencia:  ${widget.arguments.freq}",
                    style: const TextStyle(fontSize: 16),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            Visibility(
              visible: widget.arguments.sexo.isEmpty ? false : true,
              child: SizedBox(
                height: 30,
                width: MediaQuery.of(context).size.width,
                child: Center(
                  child: Text(
                    "Sexo:  ${widget.arguments.sexo}",
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}
