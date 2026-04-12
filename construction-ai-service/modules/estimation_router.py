from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response, Body
from typing import Dict
from .api_models import EstimationRequest, ReportRequest
from .estimation_engine import calculate_materials, calculate_labour
from .report_generator import generate_estimation_report
from .auth_middleware import verify_firebase_token
import pdfplumber
import io
import re

router = APIRouter()

@router.post("/estimate", dependencies=[Depends(verify_firebase_token)])
async def estimate_materials_endpoint(req: EstimationRequest):
    """Calculate materials and labour based on geometry."""
    try:
        materials = calculate_materials(req.geometry)
        labour = calculate_labour(materials, req.geometry)
        total_labour_days = sum(l["labour_days"] for l in labour.values())
        
        return {
            "projectId": req.projectId,
            "materials": materials,
            "labour": labour,
            "total_labour_days": total_labour_days,
            "confidence": "high"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-budget", dependencies=[Depends(verify_firebase_token)])
async def extract_invoice_budget(file: UploadFile = File(...)):
    """Extract budget from PDF invoice."""
    try:
        content = await file.read()
        text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        amounts = re.findall(r'(?:₹|INR|Total|Amount|Balance)\s*:?\s*([\d,]+\.?\d*)', text, re.I)
        if not amounts:
            amounts = re.findall(r'(\d{4,10}\.?\d*)', text)
        
        extracted_amount = 0.0
        if amounts:
            vals = [float(a.replace(',', '')) for a in amounts]
            extracted_amount = max(vals)
            
        return {
            "extracted_budget": extracted_amount,
            "confidence": 0.85 if extracted_amount > 0 else 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-report", dependencies=[Depends(verify_firebase_token)])
async def generate_report_endpoint(data: ReportRequest):
    """Generate high-fidelity PDF estimation report."""
    try:
        pdf_bytes = generate_estimation_report(
            project_name=data.project_name,
            geometry=data.geometry,
            materials=data.materials,
            labour=data.labour
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Estimation_{data.project_name}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
