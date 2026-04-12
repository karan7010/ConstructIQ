import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Request, HTTPException
import os

# Initialize Firebase Admin with demo safety
USE_MOCK_AUTH = True

try:
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "service_account.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            USE_MOCK_AUTH = False
            print("Firebase Admin initialized in PRODUCTION mode.")
        else:
            print("Firebase service account NOT found. Falling back to DEMO mode.")
except Exception as e:
    print(f"Auth initialization failed: {e}. Using DEMO mode.")

async def verify_firebase_token(request: Request):
    if USE_MOCK_AUTH:
        # Return a mock user for local demo stability
        return {"uid": "demo-user-123", "email": "demo@constructiq.ai"}

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
