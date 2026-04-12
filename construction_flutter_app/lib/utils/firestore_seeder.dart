import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'dart:math';

class FirestoreSeeder {
  static final _db = FirebaseFirestore.instance;

  static Future<void> seedAll() async {
    final currentUser = FirebaseAuth.instance.currentUser;
    if (currentUser == null) return;

    final uid = currentUser.uid;

    // Get ALL user IDs to ensure team visibility for everyone
    final allUsersSnap = await _db.collection('users').get();
    final allUserIds = allUsersSnap.docs.map((d) => d.id).toList();

    // ── PROJECT 1 ── Residential Complex (Stable Case)
    final p1Ref = _db.collection('projects').doc('project_demo_001');
    await p1Ref.set({
      'projectId': 'project_demo_001',
      'name': 'Block-A Residential Complex',
      'location': 'Sector 7, Jammu',
      'startDate': Timestamp.fromDate(DateTime.now().subtract(const Duration(days: 87))),
      'expectedEndDate': Timestamp.fromDate(DateTime.now().add(const Duration(days: 93))),
      'status': 'active',
      'createdBy': uid,
      'teamMembers': allUserIds, 
      'plannedBudget': _getRealisticBudget(4500000.0),
      'projectType': 'residential',
      'cadFileUrl': '',
      'estimationStatus': 'completed',
      'createdAt': Timestamp.now(),
    });

    await p1Ref.collection('estimates').doc('est_001').set({
      'estimateId': 'est_001',
      'generatedAt': Timestamp.now(),
      'cadFileName': 'block_a_ground_floor.dxf',
      'geometryData': {'totalWallArea': 342.6, 'totalFloorArea': 186.4, 'totalColumnCount': 12},
      'estimatedMaterials': {
        'cement': {'quantity': 1240, 'unit': 'bags'},
        'bricks': {'quantity': 17130, 'unit': 'nos'},
        'steel': {'quantity': 4390, 'unit': 'kg'},
        'diesel_liters': {'quantity': 350, 'unit': 'liters'},
        'sand_kg': {'quantity': 4500, 'unit': 'kg'},
      },
      'labour': {
        'brick_masonry': { 'labour_days': 43, 'trade': 'Mason', 'norm_source': 'CPWD' },
        'rcc_concrete':  { 'labour_days': 19,  'trade': 'Labourer', 'norm_source': 'CPWD' },
        'steel_fixing':  { 'labour_days': 22,  'trade': 'Steel fixer', 'norm_source': 'CPWD' },
        'plastering':    { 'labour_days': 31, 'trade': 'Plasterer', 'norm_source': 'CPWD' },
      },
      'totalLabourDays': 115,
      'disclaimer': 'Labour estimates use CPWD standard productivity norms. Actual requirements vary by team size, skill level, and site conditions.',
      'confidence': 'high',
    });

    // Seed 14 Days of Stable Resource Logs
    await _seedRealisticLogs(
      projectRef: p1Ref,
      uid: uid,
      baseDaily: {'cement': 15, 'bricks': 400, 'steel': 50},
      scenario: 'stable',
    );

    await p1Ref.collection('deviations').doc('dev_001').set({
      'deviationId': 'dev_001',
      'generatedAt': Timestamp.now(),
      'overallSeverity': 'normal',
      'mlOverrunProbability': 0.08,
      'aiInsightSummary': 'Project is healthy. Consumption patterns match CPWD norms with <3% variance.',
      'deviations': {
        'cement': {'deviationPct': 2.1, 'severity': 'normal'},
        'diesel_liters': {'deviationPct': -1.5, 'severity': 'normal'},
        'steel': {'deviationPct': 0.8, 'severity': 'normal'},
      }
    });

    // ── PROJECT 2 ── Highway Bridge (NH-44) (Chaos/Failure Case)
    final p2Ref = _db.collection('projects').doc('project_demo_002');
    await p2Ref.set({
      'projectId': 'project_demo_002',
      'name': 'NH-44 Highway Bridge Section',
      'location': 'Nagrota, Jammu',
      'startDate': Timestamp.fromDate(DateTime.now().subtract(const Duration(days: 122))),
      'expectedEndDate': Timestamp.fromDate(DateTime.now().add(const Duration(days: 58))),
      'status': 'active',
      'createdBy': uid,
      'teamMembers': allUserIds,
      'plannedBudget': _getRealisticBudget(12850000.0),
      'projectType': 'infrastructure',
      'cadFileUrl': '',
      'estimationStatus': 'completed',
      'createdAt': Timestamp.now(),
    });

    await p2Ref.collection('estimates').doc('est_002').set({
      'estimateId': 'est_002',
      'generatedAt': Timestamp.now(),
      'cadFileName': 'nh44_bridge_v2.dxf',
      'geometryData': {'bridgeLength': 150.0, 'pierCount': 4, 'deckArea': 1800.0},
      'estimatedMaterials': {
        'cement': {'quantity': 5640, 'unit': 'bags'},
        'bricks': {'quantity': 44500, 'unit': 'nos'},
        'steel': {'quantity': 26523, 'unit': 'kg'},
        'diesel_liters': {'quantity': 1800, 'unit': 'liters'},
        'sand_kg': {'quantity': 12000, 'unit': 'kg'},
      },
      'labour': {
        'brick_masonry': { 'labour_days': 111, 'trade': 'Mason', 'norm_source': 'CPWD' },
        'rcc_concrete':  { 'labour_days': 180,  'trade': 'Labourer', 'norm_source': 'CPWD' },
        'steel_fixing':  { 'labour_days': 133,  'trade': 'Steel fixer', 'norm_source': 'CPWD' },
      },
      'totalLabourDays': 424,
      'disclaimer': 'Labour estimates use CPWD standard productivity norms. Actual requirements vary by team size, skill level, and site conditions.',
      'confidence': 'medium',
    });

    // Seed 14 Days of High-Wastage Resource Logs (Spike Scenario)
    await _seedRealisticLogs(
      projectRef: p2Ref,
      uid: uid,
      baseDaily: {'cement': 45, 'bricks': 1200, 'steel': 450},
      scenario: 'spike',
    );

    await p2Ref.collection('deviations').doc('dev_002').set({
      'deviationId': 'dev_002',
      'generatedAt': Timestamp.now(),
      'overallSeverity': 'critical',
      'mlOverrunProbability': 0.94,
      'aiInsightSummary': 'CRITICAL: Severe resource leak detected. Diesel and Cement consumption spiked by >50% over the last 5 days. High probability of site theft or massive concrete wastage.',
      'deviations': {
        'cement': {'deviationPct': 58.4, 'severity': 'critical'},
        'diesel_liters': {'deviationPct': 72.1, 'severity': 'critical'},
        'steel': {'deviationPct': 1.8, 'severity': 'normal'},
      }
    });

    // ── PROJECT 3 ── Smart City Office Block (Drift/Warning Case)
    final p3Ref = _db.collection('projects').doc('project_demo_003');
    await p3Ref.set({
      'projectId': 'project_demo_003',
      'name': 'Smart City Office Block',
      'location': 'Gandhi Nagar, Jammu',
      'startDate': Timestamp.fromDate(DateTime.now().subtract(const Duration(days: 35))),
      'expectedEndDate': Timestamp.fromDate(DateTime.now().add(const Duration(days: 265))),
      'status': 'active',
      'createdBy': uid,
      'teamMembers': allUserIds,
      'plannedBudget': _getRealisticBudget(8200000.0),
      'projectType': 'commercial',
      'cadFileUrl': '',
      'estimationStatus': 'completed',
      'createdAt': Timestamp.now(),
    });

    await p3Ref.collection('estimates').doc('est_003').set({
      'estimateId': 'est_003',
      'generatedAt': Timestamp.now(),
      'cadFileName': 'smart_city_office.dxf',
      'geometryData': {'officeArea': 4500.0, 'floors': 5, 'columnCount': 24},
      'estimatedMaterials': {
        'cement': {'quantity': 3200, 'unit': 'bags'},
        'bricks': {'quantity': 25000, 'unit': 'nos'},
        'steel': {'quantity': 8500, 'unit': 'kg'},
        'diesel_liters': {'quantity': 900, 'unit': 'liters'},
        'sand_kg': {'quantity': 7500, 'unit': 'kg'},
      },
      'labour': {
        'brick_masonry': { 'labour_days': 63, 'trade': 'Mason', 'norm_source': 'CPWD' },
        'steel_fixing':  { 'labour_days': 43,  'trade': 'Steel fixer', 'norm_source': 'CPWD' },
        'plastering':    { 'labour_days': 45, 'trade': 'Plasterer', 'norm_source': 'CPWD' },
      },
      'totalLabourDays': 151,
      'disclaimer': 'Labour estimates use CPWD standard productivity norms. Actual requirements vary by team size, skill level, and site conditions.',
      'confidence': 'high',
    });

    // Seed 14 Days of Gradual Drift Resource Logs
    await _seedRealisticLogs(
      projectRef: p3Ref,
      uid: uid,
      baseDaily: {'cement': 30, 'bricks': 750, 'steel': 210},
      scenario: 'drift',
    );

    await p3Ref.collection('deviations').doc('dev_003').set({
      'deviationId': 'dev_003',
      'generatedAt': Timestamp.now(),
      'overallSeverity': 'warning',
      'mlOverrunProbability': 0.42,
      'aiInsightSummary': 'WARNING: Gradual efficiency drift detected. Sand and Brick consumption is increasing daily by ~2% over the baseline. Review supply chain quality.',
      'deviations': {
        'cement': {'deviationPct': 15.7, 'severity': 'normal'},
        'sand_kg': {'deviationPct': 32.1, 'severity': 'warning'},
        'bricks': {'deviationPct': 8.4, 'severity': 'normal'},
      }
    });
    
    // Seed Profile Data...
    await _db.collection('users').doc(uid).update({
      'designation': 'Project Director',
    });
    
    // Seed WORKFORCE
    await _seedWorkforce();

    debugPrint('✅ Firestore seeded: 3 projects with workforce, records, and profile updates');
  }

  static Future<void> _seedWorkforce() async {
    final projects = ['project_demo_001', 'project_demo_002', 'project_demo_003'];
    final trades = ['mason', 'laborer', 'helper', 'carpenter', 'steelFixer'];
    final names = ['Ramesh Kumar', 'Suresh Singh', 'Abdul Khan', 'Vijay Sharma', 'Deepak Verma', 'Sunil Dutt', 'Rajesh Gupta', 'Manoj Yadv', 'Amit Shah', 'Pawan Kalyan'];
    final random = Random();

    for (var pid in projects) {
      for (int i = 0; i < 8; i++) {
        final wid = "worker_${pid}_$i";
        final trade = trades[i % trades.length];
        
        // Vary daily rate based on trade + seniority jitter
        double baseRate = trade == 'mason' ? 850.0 : (trade == 'carpenter' ? 750.0 : 500.0);
        double dailyRate = (baseRate + random.nextInt(150)).toDouble();

        await _db.collection('workforce').doc(wid).set({
          'id': wid,
          'name': names[i % names.length],
          'trade': trade,
          'contact': '+91 90000 1000$i',
          'status': random.nextDouble() > 0.1 ? 'active' : 'onLeave', // 10% on leave
          'assignedProjectId': pid,
          'dailyRate': dailyRate,
        });
      }
    }
  }

  static Future<void> _clearCollection(CollectionReference ref) async {
    final snapshots = await ref.get();
    for (final doc in snapshots.docs) {
      await doc.reference.delete();
    }
  }

  // --- REALISM HELPERS ---

  static double _getRealisticBudget(double base) {
    // Add jitter (up to 12% variation) to make numbers look "audited"
    final random = Random();
    final jitter = base * (random.nextDouble() * 0.12);
    return (base + jitter).roundToDouble();
  }

  static Future<void> _seedRealisticLogs({
    required DocumentReference projectRef,
    required String uid,
    required Map<String, int> baseDaily,
    required String scenario,
  }) async {
    final random = Random();
    await _clearCollection(projectRef.collection('resourceLogs'));

    for (int i = 14; i >= 0; i--) {
      final logDate = DateTime.now().subtract(Duration(days: i));
      Map<String, int> materials = {};

      baseDaily.forEach((key, value) {
        double multiplier = 1.0;
        
        if (scenario == 'spike' && i <= 5) {
          // Simulate a 5-day resource spike (theft or waste)
          multiplier = 1.4 + (random.nextDouble() * 0.3);
        } else if (scenario == 'drift') {
          // Simulate gradual inefficiency drift
          multiplier = 1.0 + (i * 0.02);
        } else {
          // Normal variance (noise)
          multiplier = 0.95 + (random.nextDouble() * 0.1);
        }

        materials[key] = (value * multiplier).round();
      });

      // Add extra materials for realism
      materials['diesel_liters'] = (15 + random.nextInt(10) + (scenario == 'spike' && i <= 5 ? 20 : 0));
      materials['sand_kg'] = (200 + random.nextInt(50));

      await projectRef.collection('resourceLogs').doc('day_$i').set({
        'logId': 'log_${projectRef.id}_day_$i',
        'loggedBy': uid,
        'logDate': Timestamp.fromDate(logDate),
        'materials': materials,
        'createdAt': Timestamp.fromDate(logDate),
      });
    }
  }
}
