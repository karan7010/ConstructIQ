import joblib
from fastapi import FastAPI, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from contextlib import asynccontextmanager
import os

# Request/Response Models
class CadParseRequest(BaseModel):
    file_url: str
    projectId: str  # Matches Flutter model

class EstimationRequest(BaseModel):
    geometry: Dict[str, float]

class DeviationRequest(BaseModel):
    projectId: str  # Matches Flutter model
    period: Optional[str] = "all"
    planned_resources: Optional[Dict[str, float]] = None
    actual_resources: Optional[Dict[str, float]] = None

class PredictionRequest(BaseModel):
    projectId: str
    material_deviation_avg: Optional[float] = 0.0
    equipment_idle_ratio: Optional[float] = 0.0
    days_elapsed_pct: Optional[float] = 0.0
    budget_size: Optional[float] = 1000000.0
    project_type: Optional[str] = "Residential"

class ChatRequest(BaseModel):
    projectId: str  # Matches Flutter model
    message: str

class IndexRequest(BaseModel):
    projectId: str  # Matches Flutter model

# Lifespan for Model Loading
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists("models/cost_overrun_model.pkl"):
        print("ML model found and ready for use.")
    yield

app = FastAPI(lifespan=lifespan, title="AI Construction Planning API")

# Helper for Token Verification (Skeleton)
async def verify_token(request: Request):
    return True # For Local Demo

from modules import cad_parser, estimation_engine, deviation_analysis, ml_predictor
from modules.rag_engine import rag_engine

@app.post("/parse-cad", dependencies=[Depends(verify_token)])
async def parse_cad(req: CadParseRequest):
    geometry = cad_parser.parse_geometry("docs/sample_floor_plan.dxf")
    return {"projectId": req.projectId, "geometry": geometry}

@app.post("/estimate-materials", dependencies=[Depends(verify_token)])
async def estimate_materials(req: EstimationRequest):
    materials = estimation_engine.calculate_materials(req.geometry)
    labour = estimation_engine.calculate_labour(materials, req.geometry)
    total_labour_days = sum(l["labour_days"] for l in labour.values())
    
    return {
        "materials": materials,
        "labour": labour,
        "total_labour_days": total_labour_days,
        "confidence": "high",
        "disclaimer": "Labour estimates use CPWD standard productivity norms. Actual requirements vary by team size, skill level, and site conditions."
    }

@app.post("/analyze-deviation", dependencies=[Depends(verify_token)])
async def analyze_deviation(req: DeviationRequest):
    planned = req.planned_resources or {"cement": 100, "sand": 50, "bricks": 2000}
    actual = req.actual_resources or {"cement": 115, "sand": 48, "bricks": 2100}
    analysis = deviation_analysis.analyze_resource_usage(planned, actual)
    
    # Flatten fields for DeviationModel.fromJson in Flutter
    return {
        "projectId": req.projectId,
        "overallSeverity": analysis["overallSeverity"],
        "breakdown": analysis["breakdown"],
        "deviationPct": analysis["breakdown"].get("cement", {}).get("deviationPct", 0),
        "zScore": analysis["breakdown"].get("cement", {}).get("zScore", 0),
        "flagged": any(v.get("flagged", False) for v in analysis["breakdown"].values() if isinstance(v, dict)),
        "mlOverrunProbability": 0.15, # Placeholder for combined result
        "aiInsightSummary": f"Overall status is {analysis['overallSeverity']}. Primary deviation in cement usage."
    }

@app.post("/predict-overrun", dependencies=[Depends(verify_token)])
async def predict_overrun(req: PredictionRequest):
    type_map = {"Residential": 0, "Commercial": 1, "Infrastructure": 2}
    type_encoded = type_map.get(req.project_type, 0)
    
    data = {
        "material_deviation_avg": req.material_deviation_avg,
        "equipment_idle_ratio": req.equipment_idle_ratio,
        "days_elapsed_pct": req.days_elapsed_pct,
        "budget_size": req.budget_size,
        "project_type_encoded": type_encoded
    }
    
    probability = ml_predictor.predict_overrun(data)
    return {
        "projectId": req.projectId,
        "mlOverrunProbability": probability, 
        "riskLevel": "High" if probability > 0.6 else "Medium" if probability > 0.3 else "Low"
    }

@app.post("/ai-query", dependencies=[Depends(verify_token)])
async def ai_query(req: ChatRequest):
    answer = rag_engine.get_answer(req.projectId, req.message)
    return {"reply": answer}

@app.post("/index-project", dependencies=[Depends(verify_token)])
async def index_project(req: IndexRequest):
    count = rag_engine.index_project_data(req.projectId)
    return {"status": "indexed", "chunks_indexed": count}

@app.get("/health")
async def health():
    return {"status": "ok", "mode": "MOCK" if not os.path.exists("service_account.json") else "LIVE"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
