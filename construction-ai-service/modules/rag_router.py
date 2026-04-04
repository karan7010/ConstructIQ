from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from .rag_assistant import get_ai_response
from .auth_middleware import verify_firebase_token

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    project_context: dict = None
    project_id: str

@router.post("/ai/chat")
async def chat_with_ai(request: ChatRequest, user=Depends(verify_firebase_token)):
    """
    API endpoint for context-aware construction AI chat.
    """
    try:
        response = await get_ai_response(request.message, request.project_context)
        return {
            "projectId": request.project_id,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Chat failed: {str(e)}")
