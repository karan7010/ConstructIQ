import 'package:flutter/material.dart';

class DeviationHeatmap extends StatelessWidget {
  final Map<String, dynamic> deviations;
  const DeviationHeatmap({super.key, required this.deviations});

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('Deviation Heatmap (fl_chart implementation)'));
  }
}
