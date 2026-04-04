import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/estimation_provider.dart';

class EstimationResultsScreen extends ConsumerWidget {
  final Map<String, dynamic> geometry;
  const EstimationResultsScreen({super.key, required this.geometry});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final estimationAsync = ref.watch(estimationServiceProvider).getEstimations(geometry);

    return Scaffold(
      appBar: AppBar(title: const Text('Material Estimates')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: estimationAsync,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }

          final data = snapshot.data!;
          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              _buildEstimationCard(context, 'Bricks', '${data['bricks']} units', Icons.grid_view),
              _buildEstimationCard(context, 'Cement', '${data['cement_bags']} bags', Icons.breakfast_dining),
              _buildEstimationCard(context, 'Sand', '${data['sand_m3']} m³', Icons.grain),
              _buildEstimationCard(context, 'RCC Volume', '${data['rcc_volume_m3']} m³', Icons.foundation),
              const SizedBox(height: 24),
              const Text('Geometric Basis:', style: TextStyle(fontWeight: FontWeight.bold)),
              Text('Total Wall Length: ${geometry['total_wall_length']} m'),
              const SizedBox(height: 40),
              FilledButton(
                onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                child: const Text('Save to Project'),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildEstimationCard(BuildContext context, String label, String value, IconData icon) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Icon(icon, color: Colors.indigo),
        title: Text(label),
        trailing: Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
      ),
    );
  }
}
