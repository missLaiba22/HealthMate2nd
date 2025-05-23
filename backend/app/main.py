from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, chat_routes, profile_routes
from app.routes import register_routes 

app = FastAPI()

origins = [
    "http://localhost:5173",     # Flutter web dev server
    "http://localhost:8000",     # Local development
    "http://localhost",          # Local development
    "http://127.0.0.1",         # Local development
    "http://192.168.18.60",     # Your local IP
    "http://192.168.18.60:8000" # Your local IP with port
]

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Using specific origins instead of "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_routes.router, prefix="/auth")
app.include_router(register_routes.router, prefix="/register")
app.include_router(chat_routes.router)  # Chat routes already have prefix="/chat"
app.include_router(profile_routes.router)


# app.include_router(user_routes.router, prefix="/users")
# app.include_router(scan_routes.router, prefix="/scans")
# app.include_router(appointment_routes.router, prefix="/appointments")
# app.include_router(report_routes.router, prefix="/reports")

