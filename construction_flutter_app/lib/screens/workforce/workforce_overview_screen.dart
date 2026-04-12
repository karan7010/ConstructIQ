import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/workforce_provider.dart';
import '../../models/workforce_model.dart';
import '../../utils/design_tokens.dart';
import '../../widgets/df_card.dart';

class WorkforceOverviewScreen extends ConsumerWidget {
  final String projectId;
  const WorkforceOverviewScreen({super.key, required this.projectId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final workersAsync = ref.watch(workforceByProjectProvider(projectId));

    return Scaffold(
      backgroundColor: DFColors.background,
      appBar: AppBar(
        title: Text('Personnel Directory', style: DFTextStyles.cardTitle.copyWith(fontSize: 18)),
        backgroundColor: DFColors.surface,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Headcount Stats
            workersAsync.when(
              data: (workers) => _buildStatCard(workers),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Text('Error: $e'),
            ),
            const SizedBox(height: 32),
            _buildTradeDistribution(workersAsync.value ?? []),
            const SizedBox(height: 32),
            Text('STAFF LIST', style: DFTextStyles.labelSm),
            const SizedBox(height: 16),
            workersAsync.when(
              data: (workers) => _buildWorkerList(workers),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Text('Error: $e'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(List<WorkerModel> allWorkers) {
    return _StatCard(
      label: 'TOTAL PERSONNEL',
      value: '${allWorkers.length}',
      subLabel: 'Assigned to this project',
      icon: Icons.people_alt_rounded,
      color: DFColors.primaryStitch,
    );
  }

  Widget _buildTradeDistribution(List<WorkerModel> workers) {
    final trades = <WorkerTrade, int>{};
    for (var w in workers) {
      trades[w.trade] = (trades[w.trade] ?? 0) + 1;
    }

    return DFCard(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('TRADE BREAKDOWN', style: DFTextStyles.labelSm),
          const SizedBox(height: 16),
          ...trades.entries.map((e) => Padding(
            padding: const EdgeInsets.only(bottom: 12.0),
            child: Row(
              children: [
                Expanded(
                  flex: 2,
                  child: Text(e.key.name.toUpperCase(), style: DFTextStyles.body.copyWith(fontSize: 12, fontWeight: FontWeight.bold)),
                ),
                Expanded(
                  flex: 5,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: workers.isEmpty ? 0 : e.value / workers.length,
                      backgroundColor: DFColors.surfaceContainerLow,
                      color: DFColors.primaryStitch,
                      minHeight: 8,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text('${e.value}', style: DFTextStyles.body.copyWith(fontWeight: FontWeight.bold)),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildWorkerList(List<WorkerModel> workers) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: workers.length,
      itemBuilder: (context, index) {
        final worker = workers[index];
        
        return DFCard(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: DFColors.surfaceContainerLow,
                child: Icon(Icons.person_outline_rounded, color: DFColors.primaryStitch, size: 20),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(worker.name, style: DFTextStyles.body.copyWith(fontWeight: FontWeight.bold)),
                    Text(worker.trade.name.toUpperCase(), style: DFTextStyles.caption.copyWith(fontSize: 10)),
                  ],
                ),
              ),
              const Icon(Icons.contact_phone_outlined, color: DFColors.outlineVariant, size: 18),
            ],
          ),
        );
      },
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final String subLabel;
  final IconData icon;
  final Color color;

  const _StatCard({required this.label, required this.value, required this.subLabel, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return DFCard(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 16),
          Text(value, style: DFTextStyles.metricLarge.copyWith(height: 1.0)),
          const SizedBox(height: 4),
          Text(label, style: DFTextStyles.labelSm.copyWith(fontSize: 9, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(subLabel, style: DFTextStyles.caption.copyWith(fontSize: 10)),
        ],
      ),
    );
  }
}
