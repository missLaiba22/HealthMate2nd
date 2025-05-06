from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from app.api.ws_chat import router as ws_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("healthmate_api.log")
    ]
)

logger = logging.getLogger("healthmate")

# Create FastAPI app
app = FastAPI(
    title="HealthMate API",
    description="Backend API for HealthMate Voice Chat application",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket router
app.include_router(ws_router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "service": "HealthMate Voice Chat API"}

@app.on_event("startup")
async def startup_event():
    """Runs when the application starts"""
    logger.info("HealthMate API is starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Runs when the application shuts down"""
    logger.info("HealthMate API is shutting down")

# Run the API with uvicorn when this file is executed directly
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=True
    )