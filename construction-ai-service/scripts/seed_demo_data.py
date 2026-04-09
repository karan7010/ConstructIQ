"""
ConstructIQ — Comprehensive Database Seeder for Demo Day
=========================================================
Seeds Firestore with realistic construction project data for ALL features:
- Projects (2 active, 1 completed)
- Users (admin, manager, engineer, owner)
- Estimates (CAD-parsed material estimations)
- Resource Logs (30 days of daily logging)
- Deviations (z-score analysis snapshots)
- Vendor Bills (material purchase invoices)
- Workers (assigned workforce)
- Attendance (daily worker attendance)
- Notifications (system alerts)

Run: python scripts/seed_demo_data.py
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import random
import os
import json

# ── Firebase Init ──────────────────────────────────────────────────────
service_account_path = os.path.join(os.path.dirname(__file__), '..', 'service_account.json')
if not firebase_admin._apps:
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ── Constants ──────────────────────────────────────────────────────────
# Use the actual Firebase Auth UID of the logged-in user
DEMO_USER_UID = 'VC3G0ZmK6cTpYt7SUmcmvopF7F72'
TODAY = datetime.now()

# ── Project IDs (deterministic for reproducibility) ────────────────────
PROJECT_IDS = [
    'smart_city_office_block',
    'greenfield_residential_township',
    'highway_bridge_reconstruction',
]

# ── Helper ─────────────────────────────────────────────────────────────
def ts(dt):
    """Convert datetime to Firestore-compatible datetime."""
    return dt

def rand_between(low, high):
    return round(random.uniform(low, high), 2)

# ══════════════════════════════════════════════════════════════════════
# 1. SEED USERS
# ══════════════════════════════════════════════════════════════════════
def seed_users():
    print("  Seeding users...")
    users = [
        {
            'uid': DEMO_USER_UID,
            'name': 'Sukhshum Vaishnavi',
            'email': 'sukhshum@constructiq.dev',
            'role': 'admin',
            'phone': '+91-9419123456',
            'designation': 'Project Administrator',
            'assignedProjects': PROJECT_IDS,
            'assignedProjectId': PROJECT_IDS[0],
            'createdAt': ts(TODAY - timedelta(days=120)),
            'lastLogin': ts(TODAY),
        },
        {
            'uid': 'user_manager_karan',
            'name': 'Karan Sharma',
            'email': 'karan.sharma@constructiq.dev',
            'role': 'manager',
            'phone': '+91-9419234567',
            'designation': 'Site Manager',
            'assignedProjects': [PROJECT_IDS[0], PROJECT_IDS[1]],
            'assignedProjectId': None,
            'createdAt': ts(TODAY - timedelta(days=100)),
            'lastLogin': ts(TODAY - timedelta(hours=3)),
        },
        {
            'uid': 'user_engineer_mohit',
            'name': 'Mohit Koul',
            'email': 'mohit.koul@constructiq.dev',
            'role': 'engineer',
            'phone': '+91-9419345678',
            'designation': 'Site Engineer',
            'assignedProjects': [PROJECT_IDS[0]],
            'assignedProjectId': None,
            'createdAt': ts(TODAY - timedelta(days=90)),
            'lastLogin': ts(TODAY - timedelta(hours=1)),
        },
        {
            'uid': 'user_engineer_riya',
            'name': 'Riya Gupta',
            'email': 'riya.gupta@constructiq.dev',
            'role': 'engineer',
            'phone': '+91-9419456789',
            'designation': 'Junior Site Engineer',
            'assignedProjects': [PROJECT_IDS[1]],
            'assignedProjectId': None,
            'createdAt': ts(TODAY - timedelta(days=60)),
            'lastLogin': ts(TODAY - timedelta(hours=5)),
        },
        {
            'uid': 'user_owner_vikram',
            'name': 'Vikram Mehta',
            'email': 'vikram.mehta@jaypeegroup.in',
            'role': 'owner',
            'phone': '+91-9818123456',
            'designation': 'Project Owner',
            'assignedProjects': PROJECT_IDS,
            'assignedProjectId': PROJECT_IDS[0],
            'createdAt': ts(TODAY - timedelta(days=130)),
            'lastLogin': ts(TODAY - timedelta(days=1)),
        },
    ]
    for user in users:
        db.collection('users').document(user['uid']).set(user, merge=True)
    print(f"    ✓ {len(users)} users seeded")

# ══════════════════════════════════════════════════════════════════════
# 2. SEED PROJECTS
# ══════════════════════════════════════════════════════════════════════
def seed_projects():
    print("  Seeding projects...")
    projects = [
        {
            'projectId': 'smart_city_office_block',
            'name': 'Smart City Office Block',
            'location': 'Sector 14, Jammu Smart City',
            'startDate': ts(TODAY - timedelta(days=90)),
            'expectedEndDate': ts(TODAY + timedelta(days=180)),
            'status': 'active',
            'createdBy': DEMO_USER_UID,
            'teamMembers': [DEMO_USER_UID, 'user_manager_karan', 'user_engineer_mohit'],
            'plannedBudget': 4500000.0,
            'projectType': 'Commercial',
            'cadFileUrl': 'projects/smart_city_office_block/floor_plan_v3.dxf',
            'estimationStatus': 'completed',
            'createdAt': ts(TODAY - timedelta(days=95)),
            'ownerUserId': 'user_owner_vikram',
        },
        {
            'projectId': 'greenfield_residential_township',
            'name': 'Greenfield Residential Township',
            'location': 'Nagrota Bypass, NH-44',
            'startDate': ts(TODAY - timedelta(days=45)),
            'expectedEndDate': ts(TODAY + timedelta(days=300)),
            'status': 'active',
            'createdBy': DEMO_USER_UID,
            'teamMembers': [DEMO_USER_UID, 'user_manager_karan', 'user_engineer_riya'],
            'plannedBudget': 12000000.0,
            'projectType': 'Residential',
            'cadFileUrl': 'projects/greenfield_residential/master_plan.dxf',
            'estimationStatus': 'completed',
            'createdAt': ts(TODAY - timedelta(days=50)),
            'ownerUserId': 'user_owner_vikram',
        },
        {
            'projectId': 'highway_bridge_reconstruction',
            'name': 'Highway Bridge Reconstruction',
            'location': 'Chenani-Nashri Tunnel Approach Road',
            'startDate': ts(TODAY - timedelta(days=365)),
            'expectedEndDate': ts(TODAY - timedelta(days=30)),
            'status': 'completed',
            'createdBy': DEMO_USER_UID,
            'teamMembers': [DEMO_USER_UID, 'user_manager_karan'],
            'plannedBudget': 8500000.0,
            'projectType': 'Infrastructure',
            'cadFileUrl': 'projects/highway_bridge/bridge_elevation.dxf',
            'estimationStatus': 'completed',
            'createdAt': ts(TODAY - timedelta(days=370)),
            'ownerUserId': 'user_owner_vikram',
        },
    ]
    for proj in projects:
        db.collection('projects').document(proj['projectId']).set(proj, merge=True)
    print(f"    ✓ {len(projects)} projects seeded")

# ══════════════════════════════════════════════════════════════════════
# 3. SEED ESTIMATES (subcollection under each project)
# ══════════════════════════════════════════════════════════════════════
def seed_estimates():
    print("  Seeding estimates...")
    estimates_data = {
        'smart_city_office_block': {
            'estimateId': 'est_sc_001',
            'generatedAt': ts(TODAY - timedelta(days=85)),
            'cadFileName': 'floor_plan_v3.dxf',
            'geometryData': {
                'total_wall_length': 1240.5,
                'floor_area': 2800.0,
                'num_rooms': 42,
                'num_floors': 5,
                'wall_height': 3.2,
            },
            'estimatedMaterials': {
                'cement': {'quantity': 3200, 'unit': 'bags', 'rate': 380, 'total': 1216000},
                'sand': {'quantity': 480, 'unit': 'm³', 'rate': 1800, 'total': 864000},
                'bricks': {'quantity': 125000, 'unit': 'nos', 'rate': 8, 'total': 1000000},
                'aggregate': {'quantity': 320, 'unit': 'm³', 'rate': 2200, 'total': 704000},
                'steel': {'quantity': 45, 'unit': 'tonnes', 'rate': 58000, 'total': 2610000},
                'paint': {'quantity': 1200, 'unit': 'litres', 'rate': 350, 'total': 420000},
            },
            'confidence': 'high',
            'labour': {
                'masons': {'count': 15, 'labour_days': 180},
                'laborers': {'count': 25, 'labour_days': 270},
                'carpenters': {'count': 8, 'labour_days': 90},
                'electricians': {'count': 6, 'labour_days': 60},
                'plumbers': {'count': 4, 'labour_days': 45},
                'painters': {'count': 6, 'labour_days': 40},
            },
            'totalLabourDays': 685,
            'disclaimer': 'Estimates based on CPWD 2024 rates for J&K region. Actual requirements may vary.',
        },
        'greenfield_residential_township': {
            'estimateId': 'est_gr_001',
            'generatedAt': ts(TODAY - timedelta(days=40)),
            'cadFileName': 'master_plan.dxf',
            'geometryData': {
                'total_wall_length': 3600.0,
                'floor_area': 8500.0,
                'num_rooms': 120,
                'num_floors': 4,
                'wall_height': 3.0,
            },
            'estimatedMaterials': {
                'cement': {'quantity': 9500, 'unit': 'bags', 'rate': 380, 'total': 3610000},
                'sand': {'quantity': 1400, 'unit': 'm³', 'rate': 1800, 'total': 2520000},
                'bricks': {'quantity': 380000, 'unit': 'nos', 'rate': 8, 'total': 3040000},
                'aggregate': {'quantity': 950, 'unit': 'm³', 'rate': 2200, 'total': 2090000},
                'steel': {'quantity': 120, 'unit': 'tonnes', 'rate': 58000, 'total': 6960000},
            },
            'confidence': 'high',
            'labour': {
                'masons': {'count': 35, 'labour_days': 450},
                'laborers': {'count': 60, 'labour_days': 600},
                'carpenters': {'count': 15, 'labour_days': 200},
                'electricians': {'count': 10, 'labour_days': 150},
                'plumbers': {'count': 8, 'labour_days': 120},
            },
            'totalLabourDays': 1520,
            'disclaimer': 'Based on CPWD norms for residential construction in J&K.',
        },
        'highway_bridge_reconstruction': {
            'estimateId': 'est_hb_001',
            'generatedAt': ts(TODAY - timedelta(days=360)),
            'cadFileName': 'bridge_elevation.dxf',
            'geometryData': {
                'total_wall_length': 800.0,
                'floor_area': 1200.0,
                'num_rooms': 0,
                'num_floors': 1,
                'wall_height': 12.0,
            },
            'estimatedMaterials': {
                'cement': {'quantity': 6000, 'unit': 'bags', 'rate': 370, 'total': 2220000},
                'sand': {'quantity': 900, 'unit': 'm³', 'rate': 1700, 'total': 1530000},
                'aggregate': {'quantity': 1200, 'unit': 'm³', 'rate': 2100, 'total': 2520000},
                'steel': {'quantity': 200, 'unit': 'tonnes', 'rate': 56000, 'total': 11200000},
            },
            'confidence': 'medium',
            'labour': {
                'masons': {'count': 20, 'labour_days': 300},
                'laborers': {'count': 40, 'labour_days': 500},
                'steelFixers': {'count': 12, 'labour_days': 200},
            },
            'totalLabourDays': 1000,
            'disclaimer': 'Infrastructure estimates based on MORT&H specifications.',
        },
    }

    for pid, est in estimates_data.items():
        db.collection('projects').document(pid).collection('estimates').document(est['estimateId']).set(est)
    print(f"    ✓ {len(estimates_data)} estimates seeded")

# ══════════════════════════════════════════════════════════════════════
# 4. SEED RESOURCE LOGS (30 days for active projects)
# ══════════════════════════════════════════════════════════════════════
def seed_resource_logs():
    print("  Seeding resource logs (30 days)...")
    count = 0

    weather_options = ['Sunny', 'Cloudy', 'Light Rain', 'Windy', 'Hot', 'Clear']
    notes_options = [
        'Brickwork in progress on 2nd floor. Good progress today.',
        'Column casting completed for section B. Steel fixing started.',
        'Plastering ongoing on ground floor walls.',
        'Shuttering removed from 1st floor slab. Curing started.',
        'Electrical conduit laying in progress.',
        'Plumbing rough-in work for washrooms.',
        'Foundation excavation for block C underway.',
        'Waterproofing applied to basement walls.',
        'Tile work commenced in lobby area.',
        'RCC slab casting for terrace completed.',
        'Sand delivery received. Stockpile replenished.',
        'Safety inspection conducted. Minor issues noted.',
        'Rebar tying for beam reinforcement in section A.',
        'Paint primer coat applied on east wing.',
        'Glass installation started for front facade.',
    ]
    engineers = ['user_engineer_mohit', 'user_engineer_riya']

    for pid in ['smart_city_office_block', 'greenfield_residential_township']:
        engineer = engineers[0] if pid == 'smart_city_office_block' else engineers[1]
        for day_offset in range(30):
            log_date = TODAY - timedelta(days=day_offset)
            # Skip Sundays
            if log_date.weekday() == 6:
                continue

            # Realistic daily material usage with slight variance
            base_cement = 35 if pid == 'smart_city_office_block' else 85
            base_sand = 5.5 if pid == 'smart_city_office_block' else 12
            base_bricks = 1400 if pid == 'smart_city_office_block' else 3500
            base_aggregate = 3.5 if pid == 'smart_city_office_block' else 8

            # Add some random variance (5-15%)
            variance = lambda base: round(base * random.uniform(0.85, 1.15), 1)

            log_data = {
                'projectId': pid,
                'loggedBy': engineer,
                'date': ts(log_date),
                'materialUsage': {
                    'cement': variance(base_cement),
                    'sand': variance(base_sand),
                    'bricks': int(variance(base_bricks)),
                    'aggregate': variance(base_aggregate),
                    'steel': round(random.uniform(0.3, 1.8), 2),
                },
                'equipment': {
                    'concrete_mixer': {'hours': rand_between(4, 8), 'fuel_litres': rand_between(8, 15)},
                    'crane': {'hours': rand_between(2, 6), 'fuel_litres': rand_between(12, 25)},
                    'vibrator': {'hours': rand_between(1, 4), 'fuel_litres': rand_between(2, 5)},
                },
                'laborHours': rand_between(180, 320),
                'notes': random.choice(notes_options),
                'weatherCondition': random.choice(weather_options),
                'photoUrl': None,
                'location': {'lat': 32.7266, 'lng': 74.8570},
                'createdAt': ts(log_date),
            }

            log_id = f"log_{pid[:5]}_{30-day_offset:02d}"
            db.collection('projects').document(pid).collection('resourceLogs').document(log_id).set(log_data)
            count += 1

    print(f"    ✓ {count} resource logs seeded")

# ══════════════════════════════════════════════════════════════════════
# 5. SEED DEVIATIONS (multiple snapshots per project)
# ══════════════════════════════════════════════════════════════════════
def seed_deviations():
    print("  Seeding deviations...")
    count = 0
    deviations = [
        # Smart City — Week 1 (normal)
        {
            'pid': 'smart_city_office_block',
            'deviationId': 'dev_sc_w1',
            'projectId': 'smart_city_office_block',
            'deviationPct': 3.2,
            'zScore': 0.45,
            'flagged': False,
            'overallSeverity': 'normal',
            'mlOverrunProbability': 0.12,
            'aiInsightSummary': 'All materials within acceptable range. Cement usage tracking 3.2% above estimate — within tolerance.',
            'breakdown': {
                'cement': {'planned': 800, 'actual': 826, 'deviationPct': 3.2, 'zScore': 0.45, 'flagged': False},
                'sand': {'planned': 120, 'actual': 118, 'deviationPct': -1.7, 'zScore': -0.2, 'flagged': False},
                'bricks': {'planned': 31000, 'actual': 30500, 'deviationPct': -1.6, 'zScore': -0.15, 'flagged': False},
            },
            'generatedAt': ts(TODAY - timedelta(days=21)),
            'createdAt': ts(TODAY - timedelta(days=21)),
        },
        # Smart City — Week 3 (warning)
        {
            'pid': 'smart_city_office_block',
            'deviationId': 'dev_sc_w3',
            'projectId': 'smart_city_office_block',
            'deviationPct': 12.8,
            'zScore': 1.85,
            'flagged': True,
            'overallSeverity': 'warning',
            'mlOverrunProbability': 0.38,
            'aiInsightSummary': 'Cement consumption 12.8% above plan. Possible wastage in plastering mix. Recommend site audit.',
            'breakdown': {
                'cement': {'planned': 1600, 'actual': 1805, 'deviationPct': 12.8, 'zScore': 1.85, 'flagged': True},
                'sand': {'planned': 240, 'actual': 252, 'deviationPct': 5.0, 'zScore': 0.72, 'flagged': False},
                'bricks': {'planned': 62000, 'actual': 63100, 'deviationPct': 1.8, 'zScore': 0.22, 'flagged': False},
                'steel': {'planned': 11.5, 'actual': 12.1, 'deviationPct': 5.2, 'zScore': 0.68, 'flagged': False},
            },
            'generatedAt': ts(TODAY - timedelta(days=7)),
            'createdAt': ts(TODAY - timedelta(days=7)),
        },
        # Smart City — Latest (critical)
        {
            'pid': 'smart_city_office_block',
            'deviationId': 'dev_sc_latest',
            'projectId': 'smart_city_office_block',
            'deviationPct': 18.5,
            'zScore': 2.72,
            'flagged': True,
            'overallSeverity': 'critical',
            'mlOverrunProbability': 0.67,
            'aiInsightSummary': 'CRITICAL: Cement usage 18.5% over budget. Steel deviation at 8.3%. ML model predicts 67% overrun risk. Immediate corrective action required.',
            'breakdown': {
                'cement': {'planned': 2400, 'actual': 2844, 'deviationPct': 18.5, 'zScore': 2.72, 'flagged': True},
                'sand': {'planned': 360, 'actual': 385, 'deviationPct': 6.9, 'zScore': 1.01, 'flagged': False},
                'bricks': {'planned': 93000, 'actual': 95200, 'deviationPct': 2.4, 'zScore': 0.32, 'flagged': False},
                'steel': {'planned': 22.5, 'actual': 24.4, 'deviationPct': 8.3, 'zScore': 1.22, 'flagged': True},
            },
            'generatedAt': ts(TODAY - timedelta(days=1)),
            'createdAt': ts(TODAY - timedelta(days=1)),
        },
        # Greenfield — Latest (normal)
        {
            'pid': 'greenfield_residential_township',
            'deviationId': 'dev_gr_latest',
            'projectId': 'greenfield_residential_township',
            'deviationPct': 4.1,
            'zScore': 0.58,
            'flagged': False,
            'overallSeverity': 'normal',
            'mlOverrunProbability': 0.15,
            'aiInsightSummary': 'Project on track. Slight cement variance (4.1%) attributable to foundation depth corrections.',
            'breakdown': {
                'cement': {'planned': 3800, 'actual': 3956, 'deviationPct': 4.1, 'zScore': 0.58, 'flagged': False},
                'sand': {'planned': 560, 'actual': 548, 'deviationPct': -2.1, 'zScore': -0.3, 'flagged': False},
                'bricks': {'planned': 152000, 'actual': 149000, 'deviationPct': -2.0, 'zScore': -0.25, 'flagged': False},
            },
            'generatedAt': ts(TODAY - timedelta(days=2)),
            'createdAt': ts(TODAY - timedelta(days=2)),
        },
    ]

    for dev in deviations:
        pid = dev.pop('pid')
        db.collection('projects').document(pid).collection('deviations').document(dev['deviationId']).set(dev)
        count += 1

    print(f"    ✓ {count} deviation reports seeded")

# ══════════════════════════════════════════════════════════════════════
# 6. SEED VENDOR BILLS
# ══════════════════════════════════════════════════════════════════════
def seed_vendor_bills():
    print("  Seeding vendor bills...")
    count = 0
    vendors = [
        ('Jammu Cement Co.', 'Materials', [180000, 225000, 195000]),
        ('Sharma Sand & Aggregate', 'Materials', [85000, 92000, 78000]),
        ('NK Steel Traders', 'Materials', [320000, 450000]),
        ('Gupta Brick Kiln', 'Materials', [95000, 110000, 88000]),
        ('Royal Paint House', 'Materials', [42000, 55000]),
        ('JK Equipment Rentals', 'Equipment', [65000, 75000, 58000]),
        ('Patel Electrical Works', 'Electrical', [128000]),
        ('Vishal Plumbing Services', 'Plumbing', [95000]),
        ('ABC Transport', 'Transport', [35000, 42000, 38000]),
        ('SafeBuild Scaffolding', 'Equipment', [55000, 48000]),
    ]

    for pid in ['smart_city_office_block', 'greenfield_residential_township']:
        for vendor_name, category, amounts in vendors:
            for i, amount in enumerate(amounts):
                bill_date = TODAY - timedelta(days=random.randint(5, 80))
                bill_id = f"bill_{pid[:5]}_{vendor_name[:4].lower()}_{i}"
                bill = {
                    'id': bill_id,
                    'projectId': pid,
                    'vendorName': vendor_name,
                    'amount': float(amount),
                    'date': ts(bill_date),
                    'category': category,
                    'fileUrl': f'bills/{pid}/{bill_id}.pdf',
                    'uploadedBy': 'user_manager_karan',
                    'createdAt': ts(bill_date),
                }
                db.collection('projects').document(pid).collection('vendorBills').document(bill_id).set(bill)
                count += 1

    print(f"    ✓ {count} vendor bills seeded")

# ══════════════════════════════════════════════════════════════════════
# 7. SEED WORKERS
# ══════════════════════════════════════════════════════════════════════
def seed_workers():
    print("  Seeding workers...")
    count = 0
    worker_names = {
        'mason': ['Rajesh Kumar', 'Amit Singh', 'Deepak Dogra', 'Pawan Verma', 'Sanjay Thakur'],
        'laborer': ['Ramu Chauhan', 'Gopal Nath', 'Bharat Sharma', 'Sunil Gupta', 'Vikash Yadav',
                    'Mohan Das', 'Rakesh Pandey', 'Ashok Tiwari'],
        'carpenter': ['Harish Joiner', 'Ramesh Mistri', 'Govind Lohar'],
        'electrician': ['Anil Electricwala', 'Suresh Sharma'],
        'plumber': ['Kamal Plumber', 'Naseem Ahmad'],
        'helper': ['Ram Bahadur', 'Shankar Prasad', 'Dinesh Kumar', 'Lalchand'],
        'steelFixer': ['Mohammed Rafiq', 'Ajay Sardar'],
    }

    daily_rates = {
        'mason': 800, 'laborer': 500, 'carpenter': 750, 'electrician': 900,
        'plumber': 850, 'helper': 400, 'steelFixer': 900, 'fitter': 800,
    }

    for pid in PROJECT_IDS[:2]:
        for trade, names in worker_names.items():
            for name in names:
                worker_id = f"w_{name.split()[0].lower()}_{pid[:5]}"
                worker = {
                    'id': worker_id,
                    'name': name,
                    'trade': trade,
                    'contact': f'+91-{random.randint(7000000000, 9999999999)}',
                    'status': 'active',
                    'assignedProjectId': pid,
                    'dailyRate': float(daily_rates.get(trade, 500)),
                }
                db.collection('workers').document(worker_id).set(worker)
                count += 1

    print(f"    ✓ {count} workers seeded")

# ══════════════════════════════════════════════════════════════════════
# 8. SEED ATTENDANCE (last 14 days)
# ══════════════════════════════════════════════════════════════════════
def seed_attendance():
    print("  Seeding attendance (14 days)...")
    count = 0

    # Get all worker IDs we just seeded (for smart_city only, to limit volume)
    workers_snap = db.collection('workers').where('assignedProjectId', '==', 'smart_city_office_block').get()
    worker_ids = [w.id for w in workers_snap]

    for day_offset in range(14):
        att_date = TODAY - timedelta(days=day_offset)
        if att_date.weekday() == 6:  # Skip Sundays
            continue

        for wid in worker_ids:
            # 90% present, 5% absent, 5% partial
            roll = random.random()
            if roll < 0.90:
                status = 'present'
                check_in = att_date.replace(hour=8, minute=random.randint(0, 30))
                check_out = att_date.replace(hour=17, minute=random.randint(0, 45))
            elif roll < 0.95:
                status = 'absent'
                check_in = None
                check_out = None
            else:
                status = 'partial'
                check_in = att_date.replace(hour=10, minute=random.randint(0, 30))
                check_out = att_date.replace(hour=14, minute=random.randint(0, 30))

            att_id = f"att_{wid}_{14-day_offset:02d}"
            att = {
                'id': att_id,
                'workerId': wid,
                'projectId': 'smart_city_office_block',
                'date': ts(att_date),
                'checkIn': ts(check_in) if check_in else None,
                'checkOut': ts(check_out) if check_out else None,
                'status': status,
                'markedBy': 'user_engineer_mohit',
            }
            db.collection('attendance').document(att_id).set(att)
            count += 1

    print(f"    ✓ {count} attendance records seeded")

# ══════════════════════════════════════════════════════════════════════
# 9. SEED NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════
def seed_notifications():
    print("  Seeding notifications...")
    notifications = [
        {
            'title': 'CRITICAL: Cement Deviation Alert',
            'body': 'Smart City Office Block: Cement usage 18.5% above plan. Z-score 2.72. Immediate audit required.',
            'type': 'deviation_alert',
            'projectId': 'smart_city_office_block',
            'severity': 'critical',
            'read': False,
            'createdAt': ts(TODAY - timedelta(hours=6)),
            'userId': DEMO_USER_UID,
        },
        {
            'title': 'ML Overrun Prediction Updated',
            'body': 'Smart City project overrun probability increased to 67%. Review deviation breakdown.',
            'type': 'ml_prediction',
            'projectId': 'smart_city_office_block',
            'severity': 'warning',
            'read': False,
            'createdAt': ts(TODAY - timedelta(hours=12)),
            'userId': DEMO_USER_UID,
        },
        {
            'title': 'New Estimate Generated',
            'body': 'Greenfield Residential estimation completed successfully. Total materials valued at ₹18.2L.',
            'type': 'estimation_complete',
            'projectId': 'greenfield_residential_township',
            'severity': 'info',
            'read': True,
            'createdAt': ts(TODAY - timedelta(days=2)),
            'userId': DEMO_USER_UID,
        },
        {
            'title': 'Vendor Bill Uploaded',
            'body': 'NK Steel Traders bill for ₹4,50,000 uploaded by Karan Sharma.',
            'type': 'bill_uploaded',
            'projectId': 'smart_city_office_block',
            'severity': 'info',
            'read': True,
            'createdAt': ts(TODAY - timedelta(days=3)),
            'userId': DEMO_USER_UID,
        },
        {
            'title': 'Weekly Resource Summary',
            'body': 'Week 12 summary: 245 bags cement, 38 m³ sand, 9800 bricks consumed at Smart City site.',
            'type': 'weekly_summary',
            'projectId': 'smart_city_office_block',
            'severity': 'info',
            'read': True,
            'createdAt': ts(TODAY - timedelta(days=7)),
            'userId': DEMO_USER_UID,
        },
        {
            'title': 'Project Milestone Reached',
            'body': 'Highway Bridge Reconstruction marked as COMPLETED by Admin.',
            'type': 'project_update',
            'projectId': 'highway_bridge_reconstruction',
            'severity': 'info',
            'read': True,
            'createdAt': ts(TODAY - timedelta(days=30)),
            'userId': DEMO_USER_UID,
        },
    ]

    for i, notif in enumerate(notifications):
        db.collection('notifications').document(f'notif_{i:03d}').set(notif)
    print(f"    ✓ {len(notifications)} notifications seeded")

# ══════════════════════════════════════════════════════════════════════
# 10. SEED DASHBOARD ANALYTICS (aggregate stats)
# ══════════════════════════════════════════════════════════════════════
def seed_analytics():
    print("  Seeding dashboard analytics...")
    analytics = {
        'totalProjects': 3,
        'activeProjects': 2,
        'completedProjects': 1,
        'totalBudget': 25000000.0,
        'totalSpent': 14200000.0,
        'budgetUtilization': 56.8,
        'activeWorkers': 52,
        'avgAttendanceRate': 91.2,
        'criticalAlerts': 1,
        'pendingEstimations': 0,
        'lastUpdated': ts(TODAY),
        'monthlySpend': {
            'jan': 1200000, 'feb': 1450000, 'mar': 1680000,
            'apr': 1520000, 'may': 1750000, 'jun': 1400000,
            'jul': 1300000, 'aug': 1550000, 'sep': 1350000,
        },
        'materialConsumption': {
            'cement': {'planned': 12700, 'actual': 13625, 'unit': 'bags'},
            'sand': {'planned': 2780, 'actual': 2700, 'unit': 'm³'},
            'bricks': {'planned': 505000, 'actual': 494700, 'unit': 'nos'},
            'steel': {'planned': 365, 'actual': 381, 'unit': 'tonnes'},
        },
    }
    db.collection('analytics').document('dashboard_summary').set(analytics)
    print("    ✓ Dashboard analytics seeded")


# ══════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  ConstructIQ — Comprehensive Demo Data Seeder")
    print("=" * 60)
    print(f"  Firebase Project: aacr-a86dc")
    print(f"  Demo User UID: {DEMO_USER_UID}")
    print(f"  Timestamp: {TODAY.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    seed_users()
    seed_projects()
    seed_estimates()
    seed_resource_logs()
    seed_deviations()
    seed_vendor_bills()
    seed_workers()
    seed_attendance()
    seed_notifications()
    seed_analytics()

    print("\n" + "=" * 60)
    print("  ✅ ALL DEMO DATA SEEDED SUCCESSFULLY!")
    print("=" * 60)
    print("\n  Next steps:")
    print("  1. Restart the Python AI service")
    print("  2. Call POST /index-project for each project to populate ChromaDB")
    print("  3. Hot restart the Flutter app (press R)")
    print("  4. All features should now show realistic data\n")
