import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/estimate_model.dart';
import '../utils/constants.dart';

class EstimationService {
  final Dio _dio = Dio();
  final String _baseUrl = AppConstants.apiBaseUrl;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  Future<EstimateModel> generateEstimate(String projectId, String fileUrl) async {
    try {
      final idToken = await FirebaseAuth.instance.currentUser?.getIdToken();
      final response = await _dio.post(
        '$_baseUrl/estimate-materials',
        data: {'projectId': projectId, 'file_url': fileUrl},
        options: Options(headers: {'Authorization': 'Bearer $idToken'}),
      );
      return EstimateModel.fromJson(response.data);
    } catch (e) {
      throw Exception('Estimation failed: $e');
    }
  }

  Future<List<EstimateModel>> getProjectEstimates(String projectId) async {
    try {
      final snapshot = await _firestore
          .collection('projects')
          .doc(projectId)
          .collection('estimates')
          .orderBy('generatedAt', descending: true)
          .get();
      
      return snapshot.docs.map((doc) => EstimateModel.fromJson(doc.data())).toList();
    } catch (e) {
      throw Exception('Failed to fetch estimates: $e');
    }
  }

  // Alias for UI compatibility
  Future<EstimateModel> generateEstimation(String projectId, String fileUrl) => 
      generateEstimate(projectId, fileUrl);

  Future<Map<String, dynamic>> parseCad(String fileUrl, String projectId) async {
    try {
      final idToken = await FirebaseAuth.instance.currentUser?.getIdToken(); // Get ID token for authorization
      final response = await _dio.post(
        '$_baseUrl/parse-cad',
        data: {
          'file_url': fileUrl,
          'project_id': projectId,
        },
        options: Options(headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $idToken', // Add authorization header
        }),
      );
      if (response.statusCode == 200) {
        return response.data; // Dio automatically decodes JSON
      }
      throw Exception('Failed to parse CAD: ${response.data}');
    } catch (e) {
      throw Exception('CAD parsing error: $e');
    }
  }

  Future<Map<String, dynamic>> getEstimations(Map<String, dynamic> geometry) async {
    try {
      final idToken = await FirebaseAuth.instance.currentUser?.getIdToken(); // Get ID token for authorization
      final response = await _dio.post(
        '$_baseUrl/estimate-materials',
        data: {'geometry': geometry},
        options: Options(headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $idToken', // Add authorization header
        }),
      );
      if (response.statusCode == 200) {
        return response.data; // Dio automatically decodes JSON
      }
      throw Exception('Estimation failed: ${response.data}');
    } catch (e) {
      throw Exception('Estimation error: $e');
    }
  }
}
