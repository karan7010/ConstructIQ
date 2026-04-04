# AI-Assisted Construction Planning System Rules

## Technology Decisions
| Concern | Decision |
| :--- | :--- |
| State Management | `flutter_riverpod` ONLY |
| Navigation | `go_router` ONLY |
| Database | Firebase Cloud Firestore ONLY |
| Auth | Firebase Auth + Custom Claims |
| ML Framework | XGBoost + scikit-learn |
| Vector Store | ChromaDB (Local Persisted) |
| LLM | Gemini 1.5 Flash API |
| Embeddings | `all-MiniLM-L6-v2` |
| CAD Parsing | `ezdxf` Library |

## Firestore Schema
### /users/{userId}
- `uid`: string (doc ID)
- `name`: string
- `email`: string
- `role`: 'admin' | 'manager' | 'engineer'
- `assignedProjects`: string[]
- `createdAt`: Timestamp
- `lastLogin`: Timestamp

### /projects/{projectId}
- `projectId`: string
- `name`: string
- `location`: string
- `startDate`: Timestamp
- `expectedEndDate`: Timestamp
- `status`: 'planning' | 'active' | 'completed' | 'onhold'
- `createdBy`: string
- `teamMembers`: string[]
- `plannedBudget`: number
- `projectType`: string
- `cadFileUrl`: string
- `estimationStatus`: 'pending' | 'processing' | 'completed' | 'failed'
- `createdAt`: Timestamp

### /projects/{projectId}/estimates/{estimateId}
- `estimateId`: string
- `generatedAt`: Timestamp
- `cadFileName`: string
- `geometryData`: { totalWallArea: num, totalFloorArea: num, totalColumnCount: num, buildingHeight: num, structuralVolume: num }
- `estimatedMaterials`: { cement: { quantity: num, unit: 'bags' }, bricks: { quantity: num, unit: 'nos' }, steel: { quantity: num, unit: 'kg' }, sand: { quantity: num, unit: 'm3' }, aggregate: { quantity: num, unit: 'm3' } }
- `estimatedCost`: number
- `confidence`: 'high' | 'medium' | 'low'

### /projects/{projectId}/resourceLogs/{logId}
- `logId`: string
- `loggedBy`: string
- `logDate`: Timestamp
- `materials`: { cement: num, bricks: num, steel: num, sand: num, aggregate: num }
- `equipment`: { excavator: { used: num, idle: num }, crane: { used: num, idle: num }, mixer: { used: num, idle: num } }
- `notes`: string
- `weatherCondition`: string
- `createdAt`: Timestamp

### /projects/{projectId}/deviations/{deviationId}
- `deviationId`: string
- `generatedAt`: Timestamp
- `period`: 'daily' | 'weekly' | 'cumulative'
- `deviations`: { cement: dev_obj, bricks: dev_obj, steel: dev_obj, equipment_idle_ratio: { value: num, threshold: num, flagged: bool } }
- `overallSeverity`: 'normal' | 'warning' | 'critical'
- `mlOverrunProbability`: number
- `aiInsightSummary`: string
