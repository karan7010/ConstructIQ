from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import tempfile
import os
import httpx
from .cad_parser import parse_dxf_file
from .auth_middleware import verify_firebase_token

router = APIRouter()

class CadParseRequest(BaseModel):
    file_url: str
    project_id: str

@router.post("/cad/parse")
async def parse_cad(request: CadParseRequest, user=Depends(verify_firebase_token)):
    """
    Endpoint to parse a DXF file from a provided URL.
    Requires Firebase Authentication.
    """
    # Create a temporary file to store the downloaded DXF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
        try:
            # Download the file
            async with httpx.AsyncClient() as client:
                response = await client.get(request.file_url)
                if response.status_code != 200:
                    raise HTTPException(status_code=400, detail="Could not download file from URL")
                tmp.write(response.content)
            
            tmp_path = tmp.name
            tmp.close() # Close to allow ezdxf to read

            # Parse the file
            result = await parse_dxf_file(tmp_path)
            
            # Clean up
            os.unlink(tmp_path)
            
            return {
                "projectId": request.project_id,
                "userId": user["uid"],
                "data": result
            }
            
        except Exception as e:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise HTTPException(status_code=500, detail=f"CAD Parsing Error: {str(e)}")
