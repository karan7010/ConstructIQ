import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../utils/design_tokens.dart';

class AppShell extends StatelessWidget {
  const AppShell({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;

    int currentIndex = 0;
    if (location.startsWith('/projects')) currentIndex = 1;
    if (location.startsWith('/analytics')) currentIndex = 2;
    if (location.startsWith('/reports')) currentIndex = 3;
    if (location.startsWith('/profile')) currentIndex = 4;

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        backgroundColor: DFColors.surface,
        indicatorColor: DFColors.primaryLight,
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          switch (index) {
            case 0: context.go('/dashboard'); break;
            case 1: context.go('/projects'); break;
            case 2: context.go('/analytics'); break;
            case 3: context.go('/reports'); break;
            case 4: context.go('/profile'); break;
          }
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined, color: DFColors.textSecondary),
            selectedIcon: Icon(Icons.dashboard, color: DFColors.primary),
            label: 'Command',
          ),
          NavigationDestination(
            icon: Icon(Icons.architecture_outlined, color: DFColors.textSecondary),
            selectedIcon: Icon(Icons.architecture, color: DFColors.primary),
            label: 'Missions',
          ),
          NavigationDestination(
            icon: Icon(Icons.analytics_outlined, color: DFColors.textSecondary),
            selectedIcon: Icon(Icons.analytics, color: DFColors.primary),
            label: 'Intelligence',
          ),
          NavigationDestination(
            icon: Icon(Icons.description_outlined, color: DFColors.textSecondary),
            selectedIcon: Icon(Icons.description, color: DFColors.primary),
            label: 'Archive',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline, color: DFColors.textSecondary),
            selectedIcon: Icon(Icons.person, color: DFColors.primary),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}
