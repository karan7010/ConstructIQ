from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .deviation_analysis import analyze_deviation
from .auth_middleware import verify_firebase_token

router = APIRouter()

class DeviationRequest(BaseModel):
    estimate: dict
    logs: list
    project_id: str

@router.post("/analysis/deviation")
async def get_deviation(request: DeviationRequest, user=Depends(verify_firebase_token)):
    """
    API endpoint to analyze project deviations.
    """
    try:
        report = analyze_deviation(request.estimate, request.logs)
        return {
            "projectId": request.project_id,
            "report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
