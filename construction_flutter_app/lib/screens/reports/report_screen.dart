import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/project_provider.dart';
import '../../utils/report_generator.dart';

class ReportScreen extends ConsumerWidget {
  const ReportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectsAsync = ref.watch(userProjectsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Reports & Exports')),
      body: projectsAsync.when(
        data: (projects) {
          if (projects.isEmpty) return const Center(child: Text('No projects found.'));
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: projects.length,
            itemBuilder: (context, index) {
              final p = projects[index];
              return Card(
                child: ListTile(
                  leading: const Icon(Icons.picture_as_pdf, color: Colors.red),
                  title: Text(p.name),
                  subtitle: const Text('Managerial Summary & AI Insights'),
                  trailing: IconButton(
                    icon: const Icon(Icons.download),
                    onPressed: () => _generateTestReport(p.name),
                  ),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  void _generateTestReport(String projectName) {
    ReportGenerator.generateProjectReport(
      projectName: projectName,
      managerName: 'Admin Manager',
      summary: {
        'est_cement': 500, 'act_cement': 520, 'dev_cement': 4.0,
        'est_sand': 20, 'act_sand': 21, 'dev_sand': 5.0,
        'est_bricks': 45000, 'act_bricks': 47500, 'dev_bricks': 5.5,
        'recommendation': 'Project is healthy and on schedule.'
      },
    );
  }
}
