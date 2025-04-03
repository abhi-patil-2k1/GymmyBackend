from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from firebase_admin import auth

def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configure exception handlers for the application
    """
    
    @app.exception_handler(auth.InvalidIdTokenError)
    async def invalid_token_handler(request: Request, exc: auth.InvalidIdTokenError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid authentication token"},
        )
    
    @app.exception_handler(auth.ExpiredIdTokenError)
    async def expired_token_handler(request: Request, exc: auth.ExpiredIdTokenError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Expired authentication token"},
        )
    
    @app.exception_handler(auth.RevokedIdTokenError)
    async def revoked_token_handler(request: Request, exc: auth.RevokedIdTokenError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Revoked authentication token"},
        )
    
    @app.exception_handler(auth.UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: auth.UserNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "User not found"},
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Log the exception here
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error": str(exc)},
        )