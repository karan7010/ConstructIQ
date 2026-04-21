import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/estimation_service.dart';
import '../models/estimate_model.dart';
import '../utils/material_rates.dart';
import 'project_provider.dart';

final estimationServiceProvider = Provider<EstimationService>((ref) {
  return EstimationService();
});

final projectEstimatesProvider = StreamProvider.autoDispose.family<List<EstimateModel>, String>((ref, projectId) {
  return FirebaseFirestore.instance
      .collection('projects')
      .doc(projectId)
      .collection('estimates')
      .orderBy('generatedAt', descending: true)
      .snapshots()
      .map((snap) => snap.docs.map((doc) => EstimateModel.fromJson(doc.data())).toList());
});

final latestEstimateProvider = StreamProvider.autoDispose.family<EstimateModel?, String>((ref, projectId) {
  return FirebaseFirestore.instance
      .collection('projects')
      .doc(projectId)
      .collection('estimates')
      .orderBy('generatedAt', descending: true)
      .limit(1)
      .snapshots()
      .map((snap) => snap.docs.isEmpty ? null : EstimateModel.fromJson(snap.docs.first.data()));
});

final estimatedCostProvider = Provider.autoDispose.family<double, String>((ref, projectId) {
  final estimateAsync = ref.watch(latestEstimateProvider(projectId));
  
  return estimateAsync.maybeWhen(
    data: (estimate) {
      if (estimate == null) return 0.0;
      double total = 0.0;
      estimate.estimatedMaterials.forEach((name, data) {
        if (name == 'metadata') return;
        final qty = (data['quantity'] as num).toDouble();
        total += MaterialRates.calculateEstimatedCost(name, qty);
      });
      
      return total;
    },
    orElse: () => 0.0,
  );
});
