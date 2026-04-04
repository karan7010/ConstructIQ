import 'package:cloud_firestore/cloud_firestore.dart';

class DeviationModel {
  final String deviationId;
  final String projectId;
  final double deviationPct;
  final double zScore;
  final bool flagged;
  final String overallSeverity;
  final double mlOverrunProbability;
  final String aiInsightSummary;
  final Map<String, dynamic> breakdown;
  final DateTime createdAt;

  DeviationModel({
    required this.deviationId,
    required this.projectId,
    required this.deviationPct,
    required this.zScore,
    required this.flagged,
    required this.overallSeverity,
    required this.mlOverrunProbability,
    required this.aiInsightSummary,
    required this.breakdown,
    required this.createdAt,
  });

  factory DeviationModel.fromJson(Map<String, dynamic> json) {
    return DeviationModel(
      deviationId: json['deviationId'] as String? ?? '',
      projectId: json['projectId'] as String? ?? '',
      deviationPct: (json['deviationPct'] as num? ?? 0.0).toDouble(),
      zScore: (json['zScore'] as num? ?? 0.0).toDouble(),
      flagged: json['flagged'] as bool? ?? false,
      overallSeverity: json['overallSeverity'] as String? ?? 'normal',
      mlOverrunProbability: (json['mlOverrunProbability'] as num? ?? 0.0).toDouble(),
      aiInsightSummary: json['aiInsightSummary'] as String? ?? '',
      breakdown: json['breakdown'] as Map<String, dynamic>? ?? {},
      createdAt: (json['createdAt'] as Timestamp? ?? Timestamp.now()).toDate(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'deviationId': deviationId,
      'projectId': projectId,
      'deviationPct': deviationPct,
      'zScore': zScore,
      'flagged': flagged,
      'overallSeverity': overallSeverity,
      'mlOverrunProbability': mlOverrunProbability,
      'aiInsightSummary': aiInsightSummary,
      'breakdown': breakdown,
      'createdAt': Timestamp.fromDate(createdAt),
    };
  }
}
