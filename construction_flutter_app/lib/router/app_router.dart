import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../providers/auth_provider.dart';

import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/role_selection_screen.dart';
import '../screens/dashboard/manager_dashboard.dart';
import '../screens/dashboard/engineer_home.dart';
import '../screens/dashboard/owner_dashboard.dart';
import '../screens/projects/project_list_screen.dart';
import '../screens/projects/project_detail_screen.dart';
import '../screens/projects/create_project_screen.dart';
import '../screens/estimation/cad_upload_screen.dart';
import '../screens/logging/log_entry_screen.dart';
import '../screens/logging/log_history_screen.dart';
import '../screens/ai_assistant/ai_chat_screen.dart';
import '../screens/analytics/manager_analytics.dart';
import '../screens/reports/pdf_preview_screen.dart';
import '../screens/reports/reports_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../screens/notifications/notification_centre_screen.dart';
import '../screens/teams/team_panel_screen.dart';
import '../screens/workforce/workforce_overview_screen.dart';
import '../screens/workforce/attendance_marking_screen.dart';
import '../screens/finance/bill_upload_screen.dart';
import '../widgets/common/app_shell.dart';
import '../widgets/common/engineer_shell.dart';

// ── Navigator Keys ── created once, never recreated
final _rootNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'root');
final _shellNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'shell');

class RouterNotifier extends ChangeNotifier {
  final Ref _ref;
  RouterNotifier(this._ref) {
    _ref.listen(authStateChangesProvider, (_, __) => notifyListeners());
    _ref.listen(userProfileProvider, (_, __) => notifyListeners());
  }
}

final _routerNotifierProvider = ChangeNotifierProvider<RouterNotifier>(
  (ref) => RouterNotifier(ref),
);

// ── Single GoRouter instance ── NEVER recreated after first build
final routerProvider = Provider<GoRouter>((ref) {
  final notifier = ref.watch(_routerNotifierProvider);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    refreshListenable: notifier,
    initialLocation: '/login',
    debugLogDiagnostics: true,

    redirect: (context, state) async {
      final user = FirebaseAuth.instance.currentUser;
      final isLoggingIn = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';

      if (user == null) {
        return isLoggingIn ? null : '/login';
      }

      // Check Firestore profile exists
      final doc = await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .get();

      if (!doc.exists) {
        return '/role-selection';
      }

      final role = (doc.data()?['role'] as String? ?? 'engineer').toLowerCase();

      if (isLoggingIn || state.matchedLocation == '/role-selection') {
        if (role == 'manager' || role == 'admin') return '/dashboard';
        if (role == 'owner') return '/owner-home';
        return '/engineer-home';
      }

      return null;
    },

    routes: [
      // ── Auth routes (no shell)
      GoRoute(
        path: '/login',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/role-selection',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const RoleSelectionScreen(),
      ),

      // ── Shell with bottom nav (Manager + Admin)
      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const ManagerDashboard(),
          ),
          GoRoute(
            path: '/projects',
            builder: (context, state) => const ProjectListScreen(),
          ),
          GoRoute(
            path: '/analytics',
            builder: (context, state) => const ManagerAnalytics(),
          ),
          GoRoute(
            path: '/reports',
            builder: (context, state) => const ReportsScreen(),
          ),
          GoRoute(
            path: '/profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),

      // ── Shell for Engineer
      ShellRoute(
        navigatorKey: GlobalKey<NavigatorState>(debugLabel: 'engineerShell'),
        builder: (context, state, child) => EngineerShell(child: child),
        routes: [
          GoRoute(
            path: '/engineer-home',
            builder: (context, state) => const EngineerHome(),
          ),
          GoRoute(
            path: '/my-projects',
            builder: (context, state) => const ProjectListScreen(),
          ),
          GoRoute(
            path: '/profile-engineer',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),

      // ── Owner Route
      GoRoute(
        path: '/owner-home',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const OwnerDashboard(),
      ),

      // ── Root-level routes (no shell, full screen)
      GoRoute(
        path: '/projects/:projectId',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final pId = state.pathParameters['projectId']!;
          return ProjectDetailScreen(projectId: pId);
        },
        routes: [
          GoRoute(
            path: 'log-entry',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return LogEntryScreen(projectId: projectId);
            },
          ),
          GoRoute(
            path: 'cad-upload',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return CadUploadScreen(projectId: projectId);
            },
          ),
          GoRoute(
            path: 'ai-chat',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return AiChatScreen(projectId: projectId);
            },
          ),
          GoRoute(
            path: 'pdf-preview',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return PdfPreviewScreen(projectId: projectId);
            },
          ),
          GoRoute(
            path: 'team',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return TeamPanelScreen(projectId: projectId);
            },
          ),
          GoRoute(
            path: 'workforce',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return WorkforceOverviewScreen(projectId: projectId);
            },
          ),
          GoRoute(
            path: 'attendance',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return AttendanceMarkingScreen(projectId: projectId);
            },
          ),
          GoRoute(
            path: 'bills/upload',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final projectId = state.pathParameters['projectId']!;
              return BillUploadScreen(projectId: projectId);
            },
          ),
        ],
      ),

      GoRoute(
        path: '/create-project',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const CreateProjectScreen(),
      ),

      GoRoute(
        path: '/log-history/:projectId',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final projectId = state.pathParameters['projectId']!;
          return LogHistoryScreen(projectId: projectId);
        },
      ),


      GoRoute(
        path: '/notifications',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const NotificationCentreScreen(),
      ),
    ],
  );
});
