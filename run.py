#!/usr/bin/env python3
"""
Entry point script for running the GymBuddy API
"""
import uvicorn
import os
from app.config import settings

def main():
    """
    Run the FastAPI application
    """
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    print(f"Starting GymBuddy API on port {port}...")
    print(f"API documentation will be available at http://localhost:{port}/docs")
    
    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )

if __name__ == "__main__":
    main()