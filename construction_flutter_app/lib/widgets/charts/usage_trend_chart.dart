import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class UsageTrendChart extends StatelessWidget {
  final List<FlSpot> spots;
  const UsageTrendChart({super.key, required this.spots});

  @override
  Widget build(BuildContext context) {
    return LineChart(
      LineChartData(
        lineBarsData: [
          LineChartBarData(spots: spots, isCurved: true, color: Colors.blue),
        ],
      ),
    );
  }
}
