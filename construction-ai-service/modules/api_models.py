from pydantic import BaseModel
from typing import List, Dict, Optional

class CadParseRequest(BaseModel):
    file_url: Optional[str] = None
    projectId: str

class EstimationRequest(BaseModel):
    projectId: str
    geometry: Optional[Dict[str, float]] = None

class DeviationRequest(BaseModel):
    projectId: str
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
    projectId: str
    message: str

class IndexRequest(BaseModel):
    projectId: str

class ReportRequest(BaseModel):
    project_name: str
    geometry: Dict
    materials: Dict
    labour: Dict
