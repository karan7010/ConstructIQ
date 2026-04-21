import 'dart:io';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_storage/firebase_storage.dart';
import '../models/vendor_bill_model.dart';

class VendorBillService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;
  final FirebaseStorage _storage = FirebaseStorage.instance;

  Future<void> uploadBill({
    required VendorBillModel bill,
    required File file, // We keep the parameter to avoid breaking caller code, but ignore it
  }) async {
    try {
      // 1. Skip Storage Upload (requires paid plan)
      // Previously we attempted to upload 'file' to Firebase Storage here.
      // Since storage is not enabled on the current plan, we skip this step.
      
      String downloadUrl = ''; // Empty URL as file is not stored online

      // 2. Save Metadata to Firestore
      final billData = bill.toJson();
      billData['fileUrl'] = downloadUrl;

      await _db
          .collection('projects')
          .doc(bill.projectId)
          .collection('vendorBills')
          .doc(bill.id)
          .set(billData);
          
      print('[SUCCESS] Bill metadata saved to Firestore. Storage upload skipped.');
    } catch (e) {
      throw Exception('Failed to save bill metadata: $e');
    }
  }

  Stream<List<VendorBillModel>> getProjectBills(String projectId) {
    return _db
        .collection('projects')
        .doc(projectId)
        .collection('vendorBills')
        .orderBy('date', descending: true)
        .snapshots()
        .map((snap) => snap.docs.map((doc) => VendorBillModel.fromJson(doc.data(), doc.id)).toList());
  }

  // To show 'Recent Bills' across multiple projects on Owner Dashboard
  Stream<List<VendorBillModel>> getRecentBillsAcrossProjects(List<String> projectIds) {
    if (projectIds.isEmpty) return Stream.value([]);
    
    // Firestore has limitations on 'where' with large lists, but usually Owners have <10 projects
    return _db
        .collectionGroup('vendorBills')
        .where('projectId', whereIn: projectIds)
        .orderBy('date', descending: true)
        .limit(10)
        .snapshots()
        .map((snap) => snap.docs.map((doc) => VendorBillModel.fromJson(doc.data(), doc.id)).toList());
  }
}
