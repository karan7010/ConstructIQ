from fastapi import APIRouter, HTTPException, Depends
from .api_models import DeviationRequest
from .deviation_analysis import analyze_resource_usage
from .auth_middleware import verify_firebase_token

router = APIRouter()

@router.post("/analyze", dependencies=[Depends(verify_firebase_token)])
async def analyze_resource_deviation(req: DeviationRequest):
    """Analyze resource usage deviations against planned metrics."""
    try:
        planned = req.planned_resources or {"cement": 100, "sand": 50, "bricks": 2000}
        actual = req.actual_resources or {"cement": 115, "sand": 48, "bricks": 2100}
        
        analysis = analyze_resource_usage(planned, actual)
        
        # Flattened response for Flutter DeviationModel compatibility
        return {
            "projectId": req.projectId,
            "overallSeverity": analysis["overallSeverity"],
            "breakdown": analysis["breakdown"],
            "deviationPct": analysis["breakdown"].get("cement", {}).get("deviationPct", 0),
            "zScore": analysis["breakdown"].get("cement", {}).get("zScore", 0),
            "flagged": any(v.get("flagged", False) for v in analysis["breakdown"].values() if isinstance(v, dict)),
            "mlOverrunProbability": 0.15, 
            "aiInsightSummary": f"Overall status is {analysis['overallSeverity']}. Primary deviation in cement usage."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
