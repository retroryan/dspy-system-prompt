"""
Health check and metrics endpoints.

Provides service health status and basic metrics.
"""

import time
from datetime import datetime

from fastapi import APIRouter, Depends
from api.core.models import HealthResponse, MetricsResponse
from api.utils.config import config

router = APIRouter(prefix="", tags=["Health"])

# Track server start time
SERVER_START_TIME = time.time()

# Simple metrics tracking (for demo purposes)
class Metrics:
    """Simple metrics tracking."""
    
    def __init__(self):
        self.total_requests = 0
        self.total_queries = 0
        self.total_query_time = 0.0
        self.query_count = 0
    
    @property
    def average_query_time(self) -> float:
        """Calculate average query time."""
        if self.query_count == 0:
            return 0.0
        return self.total_query_time / self.query_count
    
    def record_query(self, execution_time: float):
        """Record a query execution."""
        self.total_queries += 1
        self.query_count += 1
        self.total_query_time += execution_time
    
    def increment_requests(self):
        """Increment request count."""
        self.total_requests += 1


# Global metrics instance
metrics = Metrics()


def get_session_count() -> int:
    """Get active session count."""
    from api.core.sessions import session_manager
    return session_manager.get_active_session_count()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the API service.
    """
    uptime = time.time() - SERVER_START_TIME
    
    return HealthResponse(
        status="healthy",
        version=config.api_version,
        uptime_seconds=uptime,
        active_sessions=get_session_count()
    )


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """
    Get server metrics.
    
    Returns current server metrics including request counts and performance data.
    """
    uptime = time.time() - SERVER_START_TIME
    
    return MetricsResponse(
        total_requests=metrics.total_requests,
        total_queries=metrics.total_queries,
        active_sessions=get_session_count(),
        average_query_time=metrics.average_query_time,
        uptime_seconds=uptime
    )