from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth, users, trainers, gym_admins, 
    social, chat, connections, 
    notifications, milestones
)
from app.core.exceptions import setup_exception_handlers

# Create FastAPI application
app = FastAPI(
    title="GymBuddy API",
    description="Backend API for GymBuddy fitness social platform",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(users.router, tags=["Users"])
app.include_router(trainers.router, tags=["Trainers"])
app.include_router(gym_admins.router, tags=["Gym Admins"])
app.include_router(social.router, tags=["Social Feed"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(connections.router, tags=["Connections"])
app.include_router(notifications.router, tags=["Notifications"])
app.include_router(milestones.router, tags=["Milestones"])

@app.get("/", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "GymBuddy API"}