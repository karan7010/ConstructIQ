import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from modules import cad_router, estimation_router, deviation_router, ml_router, rag_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model checks/loading on startup
    if os.path.exists("models/cost_overrun_model.pkl"):
        print("ML Model detected.")
    yield

app = FastAPI(
    title="ConstructIQ AI Service",
    description="Modular Advanced Construction Intelligence API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Modular Routers
app.include_router(cad_router.router, prefix="/api/cad", tags=["CAD"])
app.include_router(estimation_router.router, prefix="/api/estimation", tags=["Estimation"])
app.include_router(deviation_router.router, prefix="/api/deviation", tags=["Deviation"])
app.include_router(ml_router.router, prefix="/api/ml", tags=["ML"])
app.include_router(rag_router.router, prefix="/api/rag", tags=["RAG"])

@app.get("/health")
async def health_check():
    """System health check."""
    return {
        "status": "operational",
        "environment": "demo" if not os.path.exists("service_account.json") else "production",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
