import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/project_model.dart';

class ProjectService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  Future<void> createProject(ProjectModel project) async {
    try {
      await _db.collection('projects').doc(project.projectId).set(project.toJson());
    } catch (e) {
      throw Exception('Project creation failed: $e');
    }
  }

  Stream<List<ProjectModel>> getProjects() {
    return _db.collection('projects').snapshots().map((snapshot) {
      return snapshot.docs.map((doc) => ProjectModel.fromJson(doc.data())).toList();
    });
  }

  Future<ProjectModel?> getProjectById(String id) async {
    try {
      final doc = await _db.collection('projects').doc(id).get();
      if (doc.exists) {
        return ProjectModel.fromJson(doc.data()!);
      }
      return null;
    } catch (e) {
      throw Exception('Failed to fetch project: $e');
    }
  }

  Future<void> updateProject(ProjectModel project) async {
    try {
      await _db.collection('projects').doc(project.projectId).update(project.toJson());
    } catch (e) {
      throw Exception('Project update failed: $e');
    }
  }
}
