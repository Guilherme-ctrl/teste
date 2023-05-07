import 'package:flutter/material.dart';

class CardWidget extends StatelessWidget {
  final String nome;
  final int rank;
  final int freq;

  const CardWidget(
      {Key? key, required this.nome, required this.rank, required this.freq})
      : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: MediaQuery.of(context).size.width,
      height: 40,
      child: Padding(
        padding:
            const EdgeInsets.only(top: 8.0, bottom: 8, left: 30, right: 32),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            Container(
              height: 30,
              width: 30,
              decoration: const BoxDecoration(
                  color: Colors.blue,
                  borderRadius: BorderRadius.all(Radius.circular(100))),
              child: Center(
                child: Text(
                  "${rank.toString()}º",
                  style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Colors.white),
                ),
              ),
            ),
            const SizedBox(width: 15),
            Text(
              nome.toUpperCase(),
              style: const TextStyle(fontSize: 14, color: Colors.black),
            ),
            const Spacer(),
            Text(
              freq.toString(),
              style: const TextStyle(fontSize: 14, color: Colors.black),
            ),
            const SizedBox(width: 10),
            const Icon(
              Icons.arrow_forward_ios,
              size: 20,
              color: Colors.grey,
            )
          ],
        ),
      ),
    );
  }
}

class PriceTagPaint extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    Paint paint = Paint()
      ..color = Colors.deepPurple
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.fill;

    Path path = Path();

    path
      ..lineTo(size.width * .95, 0)
      ..lineTo(size.width, size.height / 2)
      ..lineTo(size.width * .95, size.height)
      ..lineTo(0, size.height)
      ..lineTo(0, 0)
      ..close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
