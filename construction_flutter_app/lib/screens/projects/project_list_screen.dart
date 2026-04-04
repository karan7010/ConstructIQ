import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/project_provider.dart';
import '../../utils/design_tokens.dart';
import '../../widgets/df_card.dart';
import '../../widgets/df_pill.dart';
import '../../widgets/empty_state_widget.dart';

class ProjectListScreen extends ConsumerWidget {
  const ProjectListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectsAsync = ref.watch(projectsStreamProvider);

    return Scaffold(
      backgroundColor: DFColors.background,
      body: SafeArea(
        child: projectsAsync.when(
          data: (projects) {
            return CustomScrollView(
              slivers: [
                SliverPadding(
                  padding: const EdgeInsets.fromLTRB(DFSpacing.lg, DFSpacing.lg, DFSpacing.lg, DFSpacing.md),
                  sliver: SliverToBoxAdapter(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('All Projects', style: DFTextStyles.screenTitle),
                            IconButton(
                              icon: const Icon(Icons.add_circle, color: DFColors.primary, size: 32),
                              onPressed: () => context.push('/create-project'),
                            ),
                          ],
                        ),
                        const SizedBox(height: DFSpacing.xs),
                        Text('${projects.length} active projects', style: DFTextStyles.cardSubtitle),
                      ],
                    ),
                  ),
                ),
                if (projects.isEmpty)
                  const SliverFillRemaining(
                    child: Center(
                      child: EmptyStateWidget(
                        message: 'No projects detected',
                        icon: Icons.architecture,
                      ),
                    ),
                  )
                else
                  SliverPadding(
                    padding: const EdgeInsets.symmetric(horizontal: DFSpacing.lg),
                    sliver: SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) {
                          final p = projects[index];
                          return Padding(
                            padding: const EdgeInsets.only(bottom: DFSpacing.md),
                            child: _ProjectListItem(project: p),
                          );
                        },
                        childCount: projects.length,
                      ),
                    ),
                  ),
              ],
            );
          },
          loading: () => const Center(child: CircularProgressIndicator(color: DFColors.primary)),
          error: (e, s) => Padding(
            padding: const EdgeInsets.all(32.0),
            child: Center(
              child: SingleChildScrollView(
                child: Text(
                  'STATION ERROR: $e', 
                  textAlign: TextAlign.center,
                  style: DFTextStyles.body.copyWith(color: DFColors.critical, fontWeight: FontWeight.bold)
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ProjectListItem extends StatelessWidget {
  final dynamic project;
  const _ProjectListItem({required this.project});

  @override
  Widget build(BuildContext context) {
    // Determine severity color for the left strip
    Color severityColor;
    String status = project.status.toString().toLowerCase();
    
    if (status.contains('critical') || status.contains('delayed')) {
      severityColor = DFColors.critical;
    } else if (status.contains('warning') || status.contains('risk')) {
      severityColor = DFColors.warning;
    } else {
      severityColor = DFColors.normal;
    }

    return DFCard(
      padding: EdgeInsets.zero, // We'll manage internal padding for the strip
      hasShadow: true,
      onTap: () => context.push('/projects/${project.projectId}'),
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Left Severity Strip
            Container(
              width: 6,
              decoration: BoxDecoration(
                color: severityColor,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(12),
                  bottomLeft: Radius.circular(12),
                ),
              ),
            ),
            // Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(DFSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            project.name,
                            style: DFTextStyles.cardTitle,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        DFPill(
                          label: status.toUpperCase(),
                          severity: status.contains('critical') ? 'critical' : (status.contains('warning') ? 'warning' : 'normal'),
                        ),
                      ],
                    ),
                    const SizedBox(height: DFSpacing.xs),
                    Text(project.location, style: DFTextStyles.cardSubtitle),
                    const SizedBox(height: DFSpacing.md),
                    Row(
                      children: [
                        _StatItem(label: 'BUDGET', value: '₹${project.plannedBudget}'),
                        const SizedBox(width: DFSpacing.lg),
                        _StatItem(label: 'TIMELINE', value: 'Q4 2026'),
                        const Spacer(),
                        const Icon(Icons.chevron_right, color: DFColors.textCaption, size: 20),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String value;
  const _StatItem({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: DFTextStyles.caption.copyWith(fontWeight: FontWeight.bold, fontSize: 10)),
        const SizedBox(height: 2),
        Text(value, style: DFTextStyles.body.copyWith(fontWeight: FontWeight.w600, fontSize: 13)),
      ],
    );
  }
}
