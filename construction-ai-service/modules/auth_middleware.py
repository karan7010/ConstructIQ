import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Request, HTTPException
import os

# Initialize Firebase Admin
if not firebase_admin._apps:
    # Look for service account path or use default credentials
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if cred_path:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

async def verify_firebase_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
