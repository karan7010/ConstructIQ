import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import '../models/workforce_model.dart';
import '../models/attendance_model.dart';

final workforceByProjectProvider = FutureProvider.autoDispose.family<List<WorkerModel>, String>((ref, projectId) async {
  final snap = await FirebaseFirestore.instance
      .collection('workforce')
      .where('assignedProjectId', isEqualTo: projectId)
      .get();
  
  return snap.docs.map((doc) => WorkerModel.fromJson(doc.data())).toList();
});

final dailyAttendanceProvider = FutureProvider.autoDispose.family<List<AttendanceRecord>, String>((ref, projectId) async {
  final today = DateTime.now();
  final startOfDay = DateTime(today.year, today.month, today.day);
  
  final snap = await FirebaseFirestore.instance
      .collection('attendance')
      .where('projectId', isEqualTo: projectId)
      .where('date', isEqualTo: Timestamp.fromDate(startOfDay))
      .get();
  
  return snap.docs.map((doc) => AttendanceRecord.fromJson(doc.data())).toList();
});

class WorkforceService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  Future<void> markAttendance({
    required String workerId,
    required String projectId,
    required AttendanceStatus status,
    required String markedBy,
  }) async {
    final today = DateTime.now();
    final startOfDay = DateTime(today.year, today.month, today.day);
    final attendanceId = "${workerId}_${DateFormat('yyyyMMdd').format(today)}";

    await _db.collection('attendance').doc(attendanceId).set({
      'id': attendanceId,
      'workerId': workerId,
      'projectId': projectId,
      'date': Timestamp.fromDate(startOfDay),
      'status': status.name,
      'markedBy': markedBy,
      'checkIn': status == AttendanceStatus.present ? Timestamp.fromDate(today) : null,
    }, SetOptions(merge: true));
  }
}

final workforceServiceProvider = Provider((ref) => WorkforceService());
