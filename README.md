# ConstructIQ — AI-Assisted Construction Planning & Resource Intelligence System

> Final Year B.Tech CSE Major Project | MIET (Autonomous), Jammu | Batch 2022–2026
> Team: Sukhshum Vaishnavi (2022A1R002) | Karan Sharma (2022A1R009) | Mohit Koul (2022A1R013)

---

## What This System Does

ConstructIQ is a full-stack cloud platform that connects two phases of construction:

**Planning Phase** — An architect's DXF/CAD file is uploaded. The system automatically
extracts building geometry (wall area, floor area, columns) and calculates required
material quantities (cement, bricks, steel, sand, aggregate) using standard civil
engineering quantity takeoff (QTO) formulas based on CPWD norms. Labour-days per trade
are also estimated. No cost is calculated — vendors are quoted separately.

**Execution Phase** — Site engineers log daily resource consumption via mobile app.
The system compares actual vs estimated usage, flags deviations using z-score statistical
analysis, predicts cost overrun probability using an XGBoost ML model (AUC: 0.82),
and provides project-specific answers via a RAG AI assistant (LangChain + ChromaDB + Gemini).

**Target Users:**
- **Project Owner** — The person paying for construction. Views health, deviation risk, vendor bills, team. Cannot self-register — assigned by Admin.
- **Admin** — Creates projects, uploads CAD files, manages users and role assignments.
- **Manager** — Monitors dashboard, approves vendor bills, views workforce overview, generates reports.
- **Site Engineer** — Logs daily resources with geotagged photo evidence. Read-only team view.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flutter Mobile App                           │
│  Riverpod + GoRouter + fl_chart + Firebase SDK                 │
│  Roles: Admin / Manager / Engineer / Owner                     │
└──────────────┬──────────────────────────┬──────────────────────┘
               │ Firestore streams        │ HTTP REST
               ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│   Firebase Cloud          │   │  Python FastAPI (Railway.app)    │
│  Auth + Firestore         │   │  CAD Parser (ezdxf)              │
│  Storage + Functions      │   │  Estimation Engine (CPWD QTO)    │
│  (Node.js triggers)       │   │  Deviation Analysis (z-score)    │
└──────────────────────────┘   │  XGBoost Cost Overrun Model      │
                                │  RAG AI (LangChain+ChromaDB+     │
                                │  Gemini 1.5 Flash)               │
                                └──────────────────────────────────┘
```

---

## Repository Structure

```
ConstructIQ/
├── construction_flutter_app/          ← Flutter mobile app
│   ├── lib/
│   │   ├── models/                    ← Dart model classes (fromJson/toJson)
│   │   ├── services/                  ← Firebase + API service classes
│   │   ├── providers/                 ← Riverpod providers (StreamProvider/FutureProvider)
│   │   ├── screens/
│   │   │   ├── auth/                  ← Login, Register, Role Selection
│   │   │   ├── dashboard/             ← ManagerDashboard, EngineerHome, OwnerDashboard, AdminDashboard
│   │   │   ├── projects/              ← ProjectList, ProjectDetail, CreateProject
│   │   │   ├── estimation/            ← CadUpload, EstimationResults
│   │   │   ├── logging/               ← LogEntry, LogHistory
│   │   │   ├── teams/                 ← TeamPanel, WorkforceOverview
│   │   │   ├── finance/               ← BillUpload
│   │   │   ├── reports/               ← PdfPreview
│   │   │   ├── ai/                    ← AiChat
│   │   │   ├── profile/               ← ProfileScreen
│   │   │   └── notifications/         ← NotificationCentre
│   │   ├── router/
│   │   │   └── app_router.dart        ← GoRouter with role-based redirects
│   │   ├── widgets/
│   │   │   ├── df_card.dart           ← Design system card component
│   │   │   ├── df_pill.dart           ← Severity badge component
│   │   │   ├── df_button.dart         ← Primary button component
│   │   │   └── common/
│   │   │       ├── app_shell.dart     ← Manager/Admin bottom nav shell
│   │   │       └── engineer_shell.dart ← Engineer bottom nav shell
│   │   └── utils/
│   │       ├── design_tokens.dart     ← DFColors, DFTextStyles, DFSpacing
│   │       └── firestore_seeder.dart  ← Demo data seeder (3 projects)
│   └── functions/                     ← Firebase Cloud Functions (Node.js)
│       └── index.js                   ← CAD upload trigger, role assignment
│
├── construction-ai-service/           ← Python FastAPI microservice
│   ├── main.py                        ← FastAPI app, all 7 endpoints
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env                           ← GEMINI_API_KEY, FIREBASE_CREDENTIALS_JSON (never commit)
│   ├── modules/
│   │   ├── auth_middleware.py         ← Firebase token verification
│   │   ├── cad_parser.py              ← ezdxf geometry extraction (LINE, LWPOLYLINE, ARC, SPLINE, HATCH, CIRCLE)
│   │   ├── estimation_engine.py       ← CPWD QTO formulas → material quantities + labour-days (NO COST)
│   │   ├── deviation_analysis.py      ← z-score flagging (flag if >20% OR z>2.0)
│   │   ├── ml_predictor.py            ← XGBoost inference from cost_overrun_model.pkl
│   │   └── rag_engine.py              ← LangChain + ChromaDB + Gemini 1.5 Flash RAG
│   ├── models/
│   │   └── cost_overrun_model.pkl     ← Trained XGBoost model (AUC: 0.82, 5-fold CV)
│   ├── data/
│   │   └── training_data.csv          ← 1000 synthetic construction project records
│   └── scripts/
│       ├── generate_dataset.py        ← Synthetic dataset generation with realistic noise
│       └── train_model.py             ← XGBoost training + evaluation (accuracy, AUC, CV)
│
└── README.md
```

---

## Firestore Collections

| Collection | Purpose |
|---|---|
| `/users/{uid}` | User profiles with roles (admin/manager/engineer/owner) |
| `/projects/{id}` | Project documents with teamMembers[], ownerUserId |
| `/projects/{id}/estimates/{id}` | CAD-based material quantities + CPWD labour-days |
| `/projects/{id}/resourceLogs/{id}` | Daily site logs with geotag + photoUrl |
| `/projects/{id}/deviations/{id}` | z-score deviations + ML probability + AI summary |
| `/projects/{id}/vendorBills/{id}` | Vendor invoice images + metadata |

**Key rule:** estimatedMaterials has NO cost field. Cost deliberately excluded.

---

## Python API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/parse-cad` | Parse DXF file URL → geometry |
| POST | `/estimate-materials` | Geometry → materials + labour-days |
| POST | `/analyze-deviation` | Compute z-scores + severity |
| POST | `/predict-overrun` | XGBoost → overrun probability |
| POST | `/ai-query` | RAG query → NVIDIA NIM answer (meta/llama-3.1-8b-instruct) |
| POST | `/index-project` | Index project data into ChromaDB |

All endpoints (except /health) verify Firebase ID token in Authorization header.

---

## ML Model Details

- **Algorithm:** XGBoost Classifier
- **Features:** material_deviation_avg, equipment_idle_ratio, days_elapsed_pct, budget_size, project_type_encoded
- **Target:** overrun_binary (0=no overrun, 1=overrun)
- **Dataset:** 1000 synthetic records with realistic distributions + 8% label noise
- **Performance:** Test AUC 0.82, 5-fold CV AUC 0.80 ± 0.03
- **Why 0.82 not higher:** Realistic dataset with noise. 0.98+ on synthetic data = overfitting.
- **Feature importances:** material_deviation_avg (0.38) > equipment_idle_ratio (0.26) > days_elapsed_pct (0.19)

---

## RAG AI Assistant

- **Pipeline:** Firestore data → text chunks → sentence-transformers embeddings → ChromaDB → similarity search → NVIDIA NIM (llama-3.1-8b-instruct)
- **Embedding model:** all-MiniLM-L6-v2 (384-dim vectors)
- **Vector store:** ChromaDB (one collection per project_id)
- **LLM:** NVIDIA NIM (meta/llama-3.1-8b-instruct)
- **Indexing trigger:** POST /index-project (called after new deviation analysis)
- **Key constraint:** LLM answers ONLY from retrieved project context — cannot hallucinate numbers

---

## CAD Estimation Engine

- **Parser:** ezdxf (Python library for DXF files)
- **Entities parsed:** LWPOLYLINE/LINE (walls), HATCH/closed polylines (floor), CIRCLE (columns), TEXT/MTEXT (height annotations), ARC (curved walls), SPLINE (complex curves)
- **Output:** total_wall_area (m²), total_floor_area (m²), column_count, building_height (m), structural_volume (m³)
- **Estimation formulas (CPWD norms):**
  - Bricks: wall_area × 50 (50 bricks/m²)
  - Cement masonry: wall_area × 0.3 bags/m²
  - Concrete: floor_area × 0.15 m³ (150mm M20 slab)
  - Cement concrete: concrete_vol × 8 bags/m³
  - Steel: structural_vol × 78.5 kg/m³ (1% reinforcement)
  - Labour-days: per CPWD productivity norms per trade
- **No cost output** — vendors quote separately

---

## Local Development Setup

### Prerequisites
- Flutter 3.x SDK
- Python 3.11+
- Firebase CLI (`npm install -g firebase-tools`)
- Android Studio / VS Code

### 1. Clone and configure Firebase
```bash
git clone https://github.com/Sukhshum2628/ConstructIQ.git
cd ConstructIQ/construction_flutter_app
flutter pub get
# Add your google-services.json to android/app/
flutterfire configure
```

### 2. Python microservice
```bash
cd construction-ai-service
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt

# Required: create .env file
NVIDIA_API_KEY=your_nvapi_key_here
NVIDIA_MODEL=meta/llama-3.1-8b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# Required: download service_account.json from Firebase Console
# Firebase Console → Project Settings → Service Accounts → Generate new private key
# Save as construction-ai-service/service_account.json

python main.py
# Should show: "Application startup complete" with no mock mode warnings
```

### 3. Flutter app
```bash
cd construction_flutter_app
flutter run
# Login with test accounts, use seed button to populate Firestore demo data
```

### Demo Access Keys (for development testing only)
- Admin: `ADMIN_GUTS_2026`
- Manager: `MGR_GUTS_2026`
- Engineer: `ENG_GUTS_2026`
- Owner: Assigned by Admin — cannot self-register

### Demo Projects (seeded by the app's seed button)
- **Block-A Residential Complex** — WARNING severity, 35.7% cement deviation, 67% overrun risk
- **NH-44 Highway Bridge Section** — CRITICAL severity, 62.5% cement deviation, 89% overrun risk
- **Smart City Office Block** — NORMAL severity, all materials on track, 21% overrun risk

---

## Deployment

### Flutter App
- Build: `flutter build apk --release`
- Target: Android device (physical or emulator)

### Python Microservice
- Platform: Railway.app
- Container: Docker (Dockerfile in construction-ai-service/)
- Environment variables on Railway:
  - `NVIDIA_API_KEY` — NVIDIA NIM API Key
  - `NVIDIA_MODEL` — meta/llama-3.1-8b-instruct
  - `FIREBASE_CREDENTIALS_JSON` — Full service account JSON as string
  - `PORT` — Auto-set by Railway

---

## Design System

All UI components follow the "Digital Foreman" aesthetic:
- `DFColors.primary` = #1A56A0 (command blue)
- `DFColors.warning` = #D97706 (amber)
- `DFColors.critical` = #DC2626 (red)
- `DFColors.normal` = #16A34A (green)
- Cards: white, 12dp radius, shadow only (no borders)
- Severity pills: NORMAL (green), WARNING (amber), CRITICAL (red)
- Owner role accent: #7C3AED (purple)
- No `withOpacity()` — use `.withValues(alpha:)`
- No `ConnectivityResult ==` — use `.contains(ConnectivityResult.none)`

---

## Known Architecture Decisions (do not reverse these)

1. **No vendor role** — replaced by vendor bill upload with invoice image proof
2. **No cost estimation** — material quantities only, no rupee values from CAD
3. **No log editing** — submissions are immutable for data integrity
4. **Owner cannot self-register** — Admin assigns owner role via User Management
5. **Python on Railway, not Firebase Functions** — Firebase Functions have 512MB memory limit, insufficient for XGBoost + ChromaDB + LangChain
6. **Labour output as labour-days, not headcount** — too many variables for headcount
7. **XGBoost AUC 0.82 is intentional** — realistic noise prevents overfitting

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile | Flutter 3.x, Dart, Riverpod, GoRouter, fl_chart |
| Backend | Firebase Auth, Firestore, Storage, Cloud Functions (Node.js) |
| ML/AI Service | Python, FastAPI, ezdxf, XGBoost, scikit-learn, LangChain, ChromaDB |
| LLM | NVIDIA NIM (meta/llama-3.1-8b-instruct) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Deployment | Railway.app (Python), Firebase Hosting (optional web) |
