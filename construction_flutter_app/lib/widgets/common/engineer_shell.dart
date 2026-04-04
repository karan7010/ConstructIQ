import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class EngineerShell extends StatelessWidget {
  const EngineerShell({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    int currentIndex = 0;
    if (location.startsWith('/my-projects')) currentIndex = 1;
    if (location.startsWith('/profile')) currentIndex = 2;

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          switch (index) {
            case 0: context.go('/engineer-home'); break;
            case 1: context.go('/my-projects'); break;
            case 2: context.go('/profile-engineer'); break;
          }
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.apartment_outlined),
              selectedIcon: Icon(Icons.apartment), label: 'My Projects'),
          NavigationDestination(icon: Icon(Icons.person_outline),
              selectedIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
