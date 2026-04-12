from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from .api_models import CadParseRequest
from .cad_parser import parse_from_bytes, parse_from_url
from .auth_middleware import verify_firebase_token
from .estimation_engine import calculate_materials, calculate_labour

router = APIRouter()

@router.post("/parse", dependencies=[Depends(verify_firebase_token)])
async def parse_cad(req: CadParseRequest):
    """Parse DXF from a provided URL."""
    try:
        geometry = await parse_from_url(req.file_url)
        return {"projectId": req.projectId, "geometry": geometry}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parse-upload", dependencies=[Depends(verify_firebase_token)])
async def parse_cad_upload(file: UploadFile = File(...)):
    """Analyze DXF directly via multipart upload with immediate estimation."""
    try:
        content = await file.read()
        geometry = parse_from_bytes(content)
        
        # Immediate feedback for UI
        materials = calculate_materials(geometry)
        labour = calculate_labour(materials, geometry)
        
        return {
            "geometry": geometry,
            "materials": materials,
            "labour": labour,
            "total_labour_days": sum(l["labour_days"] for l in labour.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
