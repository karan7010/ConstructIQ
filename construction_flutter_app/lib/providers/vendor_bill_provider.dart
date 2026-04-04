import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/vendor_bill_service.dart';
import '../models/vendor_bill_model.dart';
import 'project_provider.dart';

final vendorBillServiceProvider = Provider<VendorBillService>((ref) {
  return VendorBillService();
});

final projectBillsProvider = StreamProvider.family<List<VendorBillModel>, String>((ref, projectId) {
  return ref.watch(vendorBillServiceProvider).getProjectBills(projectId);
});

// For Owner Dashboard (Recent across all owned projects)
final ownerRecentBillsProvider = StreamProvider.autoDispose<List<VendorBillModel>>((ref) {
  final projectsAsync = ref.watch(userProjectsProvider);
  
  return projectsAsync.when(
    data: (projects) {
      if (projects.isEmpty) return Stream.value([]);
      final projectIds = projects.map((p) => p.projectId).toList();
      return ref.watch(vendorBillServiceProvider).getRecentBillsAcrossProjects(projectIds);
    },
    loading: () => Stream.value([]),
    error: (_, __) => Stream.value([]),
  );
});
