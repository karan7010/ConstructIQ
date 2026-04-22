import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/user_model.dart';
import '../models/project_model.dart';
import 'auth_provider.dart';

final teamMembersProvider = StreamProvider.autoDispose
    .family<List<UserModel>, String>((ref, projectId) {
  return FirebaseFirestore.instance
      .collection('projects')
      .doc(projectId)
      .snapshots()
      .asyncMap((projectDoc) async {
    if (!projectDoc.exists) return [];
    
    final memberIds = List<String>.from(projectDoc.data()?['teamMembers'] ?? []);
    if (memberIds.isEmpty) return [];

    final users = await Future.wait(
      memberIds.map((id) => FirebaseFirestore.instance
          .collection('users').doc(id).get())
    );
    
    return users
        .where((doc) => doc.exists)
        .map((doc) => UserModel.fromJson(doc.data()!))
        .toList();
  });
});

final userAssignedProjectsProvider = StreamProvider.autoDispose
    .family<List<ProjectModel>, String>((ref, userId) {
  return FirebaseFirestore.instance
      .collection('projects')
      .where('teamMembers', arrayContains: userId)
      .snapshots()
      .map((snap) => snap.docs.map((doc) => ProjectModel.fromJson(doc.data())).toList());
});

final availableTeamMembersProvider = StreamProvider.autoDispose.family<List<UserModel>, String>((ref, projectId) {
  final authState = ref.watch(authStateChangesProvider);
  final currentUid = authState.value?.uid;

  return FirebaseFirestore.instance
      .collection('projects')
      .doc(projectId)
      .snapshots()
      .asyncMap((projectDoc) async {
    final memberIds = List<String>.from(projectDoc.data()?['teamMembers'] ?? []);
    
    final usersSnap = await FirebaseFirestore.instance
        .collection('users')
        .where('role', whereIn: ['engineer', 'manager'])
        .get();

    return usersSnap.docs
        .map((doc) => UserModel.fromJson(doc.data()))
        .where((user) => user.uid != currentUid && !memberIds.contains(user.uid))
        .toList();
  });
});
