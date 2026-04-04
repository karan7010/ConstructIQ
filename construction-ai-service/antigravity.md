# AI-Assisted Construction Planning System Rules (Python)

## API Endpoints
- `POST /verify-token`: Middleware check
- `POST /parse-cad`: ezdxf geometry extraction
- `POST /estimate-materials`: Formula-based material list
- `POST /analyze-deviation`: Z-score calculation
- `POST /predict-overrun`: XGBoost inference
- `POST /ai-query`: RAG Gemini 1.5 Flash
- `POST /index-project`: ChromaDB upsert
- `GET /health`: System check

## Global Rules
1. Every endpoint MUST call `verify_firebase_token(request)` first.
2. Every request MUST use a Pydantic model for validation.
3. ML model loaded once at startup in lifespan event.
4. ChromaDB collections scoped by project ID.
