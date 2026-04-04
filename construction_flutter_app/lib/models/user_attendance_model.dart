import 'package:cloud_firestore/cloud_firestore.dart';
import 'attendance_model.dart';

class UserAttendanceRecord {
  final String id;
  final String userId;
  final String projectId;
  final DateTime date;
  final AttendanceStatus status;
  final String? markedBy;

  UserAttendanceRecord({
    required this.id,
    required this.userId,
    required this.projectId,
    required this.date,
    required this.status,
    this.markedBy,
  });

  factory UserAttendanceRecord.fromJson(Map<String, dynamic> json) {
    return UserAttendanceRecord(
      id: json['id'] as String,
      userId: json['userId'] as String,
      projectId: json['projectId'] as String,
      date: (json['date'] as Timestamp).toDate(),
      status: AttendanceStatus.values.firstWhere((e) => e.name == (json['status'] ?? 'present')),
      markedBy: json['markedBy'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'userId': userId,
      'projectId': projectId,
      'date': Timestamp.fromDate(date),
      'status': status.name,
      'markedBy': markedBy,
    };
  }
}
