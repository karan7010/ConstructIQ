class EstimationModel {
  final int cementBags;
  final double sandM3;
  final int bricksCount;
  final double aggregateM3;
  final double steelTonnes;
  final Map<String, dynamic> metadata;

  EstimationModel({
    required this.cementBags,
    required this.sandM3,
    required this.bricksCount,
    required this.aggregateM3,
    required this.steelTonnes,
    this.metadata = const {},
  });

  factory EstimationModel.fromJson(Map<String, dynamic> json) {
    return EstimationModel(
      cementBags: json['cementBags'] as int,
      sandM3: (json['sandM3'] as num).toDouble(),
      bricksCount: json['bricksCount'] as int,
      aggregateM3: (json['aggregateM3'] as num).toDouble(),
      steelTonnes: (json['steelTonnes'] as num).toDouble(),
      metadata: json['metadata'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'cementBags': cementBags,
      'sandM3': sandM3,
      'bricksCount': bricksCount,
      'aggregateM3': aggregateM3,
      'steelTonnes': steelTonnes,
      'metadata': metadata,
    };
  }
}
