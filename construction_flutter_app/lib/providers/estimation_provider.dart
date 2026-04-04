import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/estimation_service.dart';
import '../models/estimate_model.dart';

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
