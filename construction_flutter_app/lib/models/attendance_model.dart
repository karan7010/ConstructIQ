import 'package:cloud_firestore/cloud_firestore.dart';

enum AttendanceStatus { present, absent, partial }

class AttendanceRecord {
  final String id;
  final String workerId;
  final String projectId;
  final DateTime date;
  final DateTime? checkIn;
  final DateTime? checkOut;
  final AttendanceStatus status;
  final String? markedBy; // UID of Engineer

  AttendanceRecord({
    required this.id,
    required this.workerId,
    required this.projectId,
    required this.date,
    this.checkIn,
    this.checkOut,
    required this.status,
    this.markedBy,
  });

  factory AttendanceRecord.fromJson(Map<String, dynamic> json) {
    return AttendanceRecord(
      id: json['id'] as String,
      workerId: json['workerId'] as String,
      projectId: json['projectId'] as String,
      date: (json['date'] as Timestamp).toDate(),
      checkIn: (json['checkIn'] as Timestamp?)?.toDate(),
      checkOut: (json['checkOut'] as Timestamp?)?.toDate(),
      status: AttendanceStatus.values.firstWhere((e) => e.name == (json['status'] ?? 'present')),
      markedBy: json['markedBy'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'workerId': workerId,
      'projectId': projectId,
      'date': Timestamp.fromDate(date),
      'checkIn': checkIn != null ? Timestamp.fromDate(checkIn!) : null,
      'checkOut': checkOut != null ? Timestamp.fromDate(checkOut!) : null,
      'status': status.name,
      'markedBy': markedBy,
    };
  }
}
