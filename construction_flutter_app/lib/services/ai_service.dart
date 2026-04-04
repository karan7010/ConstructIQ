import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../utils/constants.dart';

class AiService {
  final Dio _dio = Dio();
  final String _baseUrl = AppConstants.apiBaseUrl;

  Future<Map<String, dynamic>> queryAi(String projectId, String question) async {
    try {
      final idToken = await FirebaseAuth.instance.currentUser?.getIdToken();
      final response = await _dio.post(
        '$_baseUrl/ai-query',
        data: {
          'projectId': projectId,
          'message': question, // Consistent with ChatRequest Pydantic model
          'user_id': FirebaseAuth.instance.currentUser?.uid,
        },
        options: Options(headers: {'Authorization': 'Bearer $idToken'}),
      );
      return response.data;
    } catch (e) {
      throw Exception('AI Assistant query failed: $e');
    }
  }

  Future<String> getChatResponse(String message, {String? projectId}) async {
    try {
      final idToken = await FirebaseAuth.instance.currentUser?.getIdToken();
      final response = await _dio.post(
        '$_baseUrl/ai-query',
        data: {
          'projectId': projectId ?? 'general',
          'message': message,
        },
        options: Options(headers: {'Authorization': 'Bearer $idToken'}),
      );
      if (response.statusCode == 200) {
        return response.data['reply'];
      }
      throw Exception('Chat failed');
    } catch (e) {
      throw Exception('AI error: $e');
    }
  }

  Future<void> indexProject(String projectId) async {
    try {
      final idToken = await FirebaseAuth.instance.currentUser?.getIdToken();
      await _dio.post(
        '$_baseUrl/index-project',
        data: {'project_id': projectId},
        options: Options(headers: {'Authorization': 'Bearer $idToken'}),
      );
    } catch (e) {
      throw Exception('Project indexing failed: $e');
    }
  }
}
