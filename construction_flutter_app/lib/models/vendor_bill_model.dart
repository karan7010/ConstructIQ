import 'package:cloud_firestore/cloud_firestore.dart';

class VendorBillModel {
  final String id;
  final String projectId;
  final String vendorName;
  final double amount;
  final DateTime date;
  final String category;
  final String fileUrl;
  final String uploadedBy;
  final DateTime createdAt;

  VendorBillModel({
    required this.id,
    required this.projectId,
    required this.vendorName,
    required this.amount,
    required this.date,
    required this.category,
    required this.fileUrl,
    required this.uploadedBy,
    required this.createdAt,
  });

  factory VendorBillModel.fromJson(Map<String, dynamic> json, [String? docId]) {
    return VendorBillModel(
      id: docId ?? json['id'] as String? ?? '',
      projectId: json['projectId'] as String? ?? '',
      vendorName: json['vendorName'] as String? ?? 'Miscellaneous',
      amount: (json['amount'] as num? ?? 0.0).toDouble(),
      date: (json['date'] as Timestamp?)?.toDate() ?? DateTime.now(),
      category: json['category'] as String? ?? 'Other',
      fileUrl: json['fileUrl'] as String? ?? '',
      uploadedBy: json['uploadedBy'] as String? ?? 'Admin',
      createdAt: (json['createdAt'] as Timestamp? ?? Timestamp.now()).toDate(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'projectId': projectId,
      'vendorName': vendorName,
      'amount': amount,
      'date': Timestamp.fromDate(date),
      'category': category,
      'fileUrl': fileUrl,
      'uploadedBy': uploadedBy,
      'createdAt': Timestamp.fromDate(createdAt),
    };
  }
}
