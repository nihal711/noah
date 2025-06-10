from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models
from routers import auth, users, leave, bank_letter, visa_letter, requests, payslips, salary_benefits
from sqlalchemy import text

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app with custom documentation
app = FastAPI(
    title="Noah HR Management API",
    description="""
    A comprehensive HR Management API with the following features:
    
    ## Authentication
    * Login and logout functionality
    * JWT token-based authentication
    
    ## User Management
    * Create and manage user accounts
    * Employee information management
    
    ## Leave Management
    * Apply for leave
    * View leave requests and status
    * Check leave balance
    * Approve/reject leave requests (manager function)
    
    ## Bank Letter Requests
    * Request bank letters for various purposes
    * Track request status
    * HR approval workflow
    * File attachments support
    
    ## Visa Letter Requests
    * Request visa letters for different countries
    * Track request status
    * HR approval workflow
    * File attachments support
    
    ## Request Management
    * View all requests across different types
    * Unified request tracking
    * Pending requests dashboard
    
    ## Demo Environment
    This is a demo environment with PostgreSQL database integration.
    All data is stored persistently in the 'noah' database.
    """,
    version="1.0.0",
    contact={
        "name": "Nihal",
        "email": "nihal@optioai.tech",
    },
    license_info={
        "name": "MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leave.router)
app.include_router(bank_letter.router)
app.include_router(visa_letter.router)
app.include_router(requests.router)
app.include_router(payslips.router)
app.include_router(salary_benefits.router)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information and health check.
    """
    return {
        "message": "Welcome to Noah HR Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "healthy"
    }

@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database connectivity.
    """
    try:
        # Simple database query to check connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "message": "All systems operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181) 