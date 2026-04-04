from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .ml_predictor import predict_completion_cost
from .auth_middleware import verify_firebase_token

router = APIRouter()

class MLPredictRequest(BaseModel):
    current_data: dict
    initial_estimate: float = 100000
    project_id: str

@router.post("/ml/predict-cost")
async def get_cost_prediction(request: MLPredictRequest, user=Depends(verify_firebase_token)):
    """
    API endpoint for ML-based project cost forecasting.
    """
    try:
        prediction = predict_completion_cost(request.current_data, request.initial_estimate)
        return {
            "projectId": request.project_id,
            "prediction": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Prediction failed: {str(e)}")
