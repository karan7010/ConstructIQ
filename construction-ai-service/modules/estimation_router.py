from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .estimation_engine import generate_estimate
from .auth_middleware import verify_firebase_token

router = APIRouter()

class EstimationRequest(BaseModel):
    geometry_data: dict
    params: dict = {}
    project_id: str

@router.post("/estimation/generate")
async def get_estimation(request: EstimationRequest, user=Depends(verify_firebase_token)):
    """
    Generate a material estimation based on geometry and project parameters.
    """
    try:
        results = generate_estimate(request.geometry_data, request.params)
        return {
            "projectId": request.project_id,
            "userId": user["uid"],
            "estimate": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estimation failed: {str(e)}")
