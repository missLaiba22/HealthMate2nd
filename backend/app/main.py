from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, chat_routes, profile_routes, appointment_routes, scan_routes, speech_routes

app = FastAPI(title="HealthMate API", version="1.0.0")

# CORS configuration
origins = [
    "http://localhost:5173",     # Flutter web dev server
    "http://localhost:8000",     # Local development
    "http://localhost",          # Local development
    "http://127.0.0.1",         # Local development
    "http://192.168.137.221",    # Your current IP
    "http://192.168.137.221:8000", # Your current IP with port
    "http://10.115.103.69",      # Previous IP (fallback)
    "http://10.115.103.69:8000", # Previous IP with port (fallback)
    "http://192.168.18.60",      # Previous IP (fallback)
    "http://192.168.18.60:8000", # Previous IP with port (fallback)
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
