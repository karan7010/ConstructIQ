import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import '../models/user_attendance_model.dart';
import '../models/attendance_model.dart';

final userDailyAttendanceProvider = StreamProvider.autoDispose.family<List<UserAttendanceRecord>, String>((ref, projectId) {
  final today = DateTime.now();
  final startOfDay = DateTime(today.year, today.month, today.day);
  
  return FirebaseFirestore.instance
      .collection('user_attendance')
      .where('projectId', isEqualTo: projectId)
      .where('date', isEqualTo: Timestamp.fromDate(startOfDay))
      .snapshots()
      .map((snap) => snap.docs.map((doc) => UserAttendanceRecord.fromJson(doc.data())).toList());
});

class UserAttendanceService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  Future<void> markUserAttendance({
    required String uid,
    required String projectId,
    required AttendanceStatus status,
    required String markedBy,
  }) async {
    final today = DateTime.now();
    final startOfDay = DateTime(today.year, today.month, today.day);
    final attendanceId = "${uid}_${DateFormat('yyyyMMdd').format(today)}";

    await _db.collection('user_attendance').doc(attendanceId).set({
      'id': attendanceId,
      'userId': uid,
      'projectId': projectId,
      'date': Timestamp.fromDate(startOfDay),
      'status': status.name,
      'markedBy': markedBy,
    }, SetOptions(merge: true));
  }
}

final userAttendanceServiceProvider = Provider((ref) => UserAttendanceService());
