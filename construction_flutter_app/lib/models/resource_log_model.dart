import 'package:cloud_firestore/cloud_firestore.dart';

class ResourceLogModel {
  final String id;
  final String projectId;
  final String loggedBy;
  final DateTime date;
  final Map<String, double> materialUsage;
  final Map<String, Map<String, double>> equipment;
  final double laborHours;
  final String notes;
  final String weatherCondition;
  final String? photoUrl;
  final Map<String, double>? location;
  final DateTime createdAt;

  ResourceLogModel({
    required this.id,
    required this.projectId,
    required this.loggedBy,
    required this.date,
    required this.materialUsage,
    required this.equipment,
    required this.laborHours,
    required this.notes,
    required this.weatherCondition,
    this.photoUrl,
    this.location,
    required this.createdAt,
  });

  // Aliases for Service/JSON compatibility
  String get logId => id;
  DateTime get logDate => date;
  Map<String, double> get materials => materialUsage;

  factory ResourceLogModel.fromJson(Map<String, dynamic> json, [String? docId]) {
    return ResourceLogModel(
      id: docId ?? json['id'] as String? ?? json['logId'] as String? ?? '',
      projectId: json['projectId'] as String? ?? '',
      loggedBy: json['loggedBy'] as String? ?? 'Unknown',
      date: (json['date'] as Timestamp?)?.toDate() ?? 
            (json['logDate'] as Timestamp?)?.toDate() ?? DateTime.now(),
      materialUsage: Map<String, double>.from(json['materialUsage'] ?? json['materials'] ?? {}),
      equipment: Map<String, Map<String, dynamic>>.from(json['equipment'] ?? {}).map(
        (k, v) => MapEntry(k, Map<String, double>.from(v)),
      ),
      laborHours: (json['laborHours'] as num? ?? 0.0).toDouble(),
      notes: json['notes'] as String? ?? '',
      weatherCondition: json['weatherCondition'] as String? ?? 'Sunny',
      photoUrl: json['photoUrl'] as String?,
      location: json['location'] != null ? Map<String, double>.from(json['location']) : null,
      createdAt: (json['createdAt'] as Timestamp? ?? Timestamp.now()).toDate(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'projectId': projectId,
      'loggedBy': loggedBy,
      'date': Timestamp.fromDate(date),
      'materialUsage': materialUsage,
      'equipment': equipment,
      'laborHours': laborHours,
      'notes': notes,
      'weatherCondition': weatherCondition,
      'photoUrl': photoUrl,
      'location': location,
      'createdAt': Timestamp.fromDate(createdAt),
    };
  }
}
