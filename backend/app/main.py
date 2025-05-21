from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth_routes, chat_routes, profile_routes
from app.routes import register_routes 
app = FastAPI()
origins = [
    "http://localhost:5173",  # Your Flutter web dev server origin, adjust port if needed
    "http://localhost:8000",  # If your frontend and backend run on same origin, optional
    "http://localhost",       # You can also allow all localhost variants
    "http://127.0.0.1",
]

# CORS for Flutter frontend (adjust origin if hosted differently)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only. Use exact domain in production.
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

