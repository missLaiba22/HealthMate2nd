from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, chat_routes, profile_routes, appointment_routes, scan_routes, speech_routes
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HealthMate API", version="1.0.0")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Process time: {process_time:.4f}s")
    
    return response

# CORS configuration
origins = [
    "http://localhost:5173",     # Flutter web dev server
    "http://localhost:8000",     # Local development
    "http://localhost",          # Local development
    "http://127.0.0.1",         # Local development
    "http://192.168.18.60",      # Current IP
    "http://192.168.18.60:8000", # Current IP with port
    "http://192.168.137.221",    # Previous IP (fallback)
    "http://192.168.137.221:8000", # Previous IP with port (fallback)
    "http://10.115.103.69",      # Previous IP (fallback)
    "http://10.115.103.69:8000", # Previous IP with port (fallback)
    "http://172.20.6.241",      # Previous IP (fallback)
    "http://172.20.6.241:8000" # Previous IP with port (fallback)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes with consistent prefixes
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat_routes.router, prefix="/chat", tags=["Chat"])
app.include_router(profile_routes.router, prefix="/profile", tags=["Profile"])
app.include_router(appointment_routes.router, prefix="/appointments", tags=["Appointments"])
app.include_router(scan_routes.router, prefix="/scan", tags=["Scan Analysis"])
app.include_router(speech_routes.router, prefix="/speech", tags=["Speech"])

@app.get("/")
async def root():
    return {"message": "HealthMate API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "HealthMate API is operational"}
