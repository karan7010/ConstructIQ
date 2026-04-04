import 'package:cloud_firestore/cloud_firestore.dart';

enum ProjectStatus { planning, active, completed, onhold }
enum EstimationStatus { pending, processing, completed, failed }

class ProjectModel {
  final String projectId;
  final String name;
  final String location;
  final DateTime startDate;
  final DateTime expectedEndDate;
  final ProjectStatus status;
  final String createdBy;
  final List<String> teamMembers;
  final double plannedBudget;
  final String projectType;
  final String cadFileUrl;
  final EstimationStatus estimationStatus;
  final DateTime createdAt;
  final String? ownerUserId;

  // Getters for UI compatibility
  String get id => projectId;
  Map<String, dynamic> get cadMetadata => {
    'total_wall_length': 0.0,
    'floor_area': 0.0,
    'file_name': cadFileUrl.split('/').last,
  };

  ProjectModel({
    required this.projectId,
    required this.name,
    required this.location,
    required this.startDate,
    required this.expectedEndDate,
    required this.status,
    required this.createdBy,
    required this.teamMembers,
    required this.plannedBudget,
    required this.projectType,
    required this.cadFileUrl,
    required this.estimationStatus,
    required this.createdAt,
    this.ownerUserId,
  });

  factory ProjectModel.fromJson(Map<String, dynamic> json) {
    return ProjectModel(
      projectId: json['projectId'] as String,
      name: json['name'] as String,
      location: json['location'] as String,
      startDate: (json['startDate'] as Timestamp).toDate(),
      expectedEndDate: (json['expectedEndDate'] as Timestamp).toDate(),
      status: ProjectStatus.values.firstWhere((e) => e.name == json['status']),
      createdBy: json['createdBy'] as String,
      teamMembers: List<String>.from(json['teamMembers'] ?? []),
      plannedBudget: (json['plannedBudget'] as num).toDouble(),
      projectType: json['projectType'] as String,
      cadFileUrl: json['cadFileUrl'] as String,
      estimationStatus: EstimationStatus.values.firstWhere((e) => e.name == json['estimationStatus']),
      createdAt: (json['createdAt'] as Timestamp).toDate(),
      ownerUserId: json['ownerUserId'] as String?,
    );
  }

  ProjectModel copyWith({
    String? projectId,
    String? name,
    String? location,
    DateTime? startDate,
    DateTime? expectedEndDate,
    ProjectStatus? status,
    String? createdBy,
    List<String>? teamMembers,
    double? plannedBudget,
    String? projectType,
    String? cadFileUrl,
    EstimationStatus? estimationStatus,
    DateTime? createdAt,
    String? ownerUserId,
  }) {
    return ProjectModel(
      projectId: projectId ?? this.projectId,
      name: name ?? this.name,
      location: location ?? this.location,
      startDate: startDate ?? this.startDate,
      expectedEndDate: expectedEndDate ?? this.expectedEndDate,
      status: status ?? this.status,
      createdBy: createdBy ?? this.createdBy,
      teamMembers: teamMembers ?? this.teamMembers,
      plannedBudget: plannedBudget ?? this.plannedBudget,
      projectType: projectType ?? this.projectType,
      cadFileUrl: cadFileUrl ?? this.cadFileUrl,
      estimationStatus: estimationStatus ?? this.estimationStatus,
      createdAt: createdAt ?? this.createdAt,
      ownerUserId: ownerUserId ?? this.ownerUserId,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'projectId': projectId,
      'name': name,
      'location': location,
      'startDate': Timestamp.fromDate(startDate),
      'expectedEndDate': Timestamp.fromDate(expectedEndDate),
      'status': status.name,
      'createdBy': createdBy,
      'teamMembers': teamMembers,
      'plannedBudget': plannedBudget,
      'projectType': projectType,
      'cadFileUrl': cadFileUrl,
      'estimationStatus': estimationStatus.name,
      'createdAt': Timestamp.fromDate(createdAt),
      'ownerUserId': ownerUserId,
    };
  }
}
