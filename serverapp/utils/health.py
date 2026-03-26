"""
Health check endpoints for monitoring service health
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import time


class HealthCheck:
    """Health check utility for all services"""
    
    @staticmethod
    def database_health(db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start = time.time()
            db.execute(text("SELECT 1"))
            duration = time.time() - start
            
            return {
                "status": "healthy",
                "duration_ms": round(duration * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def app_health() -> Dict[str, Any]:
        """Check application health"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "mini-uber-api"
        }
    
    @staticmethod
    def overall_health(db: Optional[Session] = None) -> Dict[str, Any]:
        """Get overall system health"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "app": HealthCheck.app_health()
            }
        }
        
        if db:
            health_status["checks"]["database"] = HealthCheck.database_health(db)
            
            # If any check is unhealthy, overall status is unhealthy
            if any(check.get("status") == "unhealthy" for check in health_status["checks"].values()):
                health_status["status"] = "unhealthy"
        
        return health_status
