"""
Enhanced system administration endpoints.

Provides detailed system metrics, health status, and administrative actions.
"""

import logging

from fastapi import APIRouter, HTTPException, status, Depends
from api.core.config_models import (
    SystemHealthStatus, SystemMetrics, SystemActionRequest, SystemActionResponse
)
from api.core.config_manager import ConfigManager
from api.core.demo_executor import DemoExecutor
from api.core.dependencies import get_config_manager, get_demo_executor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System Administration"])


@router.get("/status", response_model=SystemHealthStatus)
def get_system_status(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Get detailed system health status.
    
    Provides comprehensive system health information including
    CPU usage, memory usage, active connections, and overall status.
    
    Returns:
        Detailed system health status
    """
    try:
        return config_manager.get_system_health()
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system status: {str(e)}"
        )


@router.get("/metrics", response_model=SystemMetrics)
def get_enhanced_metrics(
    config_manager: ConfigManager = Depends(get_config_manager),
    demo_executor: DemoExecutor = Depends(get_demo_executor)
):
    """
    Get enhanced system metrics.
    
    Provides detailed system metrics including resource usage,
    demo statistics, tool execution counts, and performance data.
    
    Returns:
        Enhanced system metrics
    """
    try:
        return config_manager.get_system_metrics(demo_executor)
    except Exception as e:
        logger.error(f"Failed to get enhanced metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system metrics: {str(e)}"
        )


@router.post("/actions", response_model=SystemActionResponse)
def perform_system_action(
    request: SystemActionRequest,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Perform a system administrative action.
    
    Executes system actions such as restarting services, clearing caches,
    exporting diagnostics, or viewing logs.
    
    Args:
        request: System action parameters
        
    Returns:
        Action execution result
        
    Raises:
        400: Invalid action or parameters
        500: Action execution failure
    """
    try:
        result = config_manager.perform_system_action(
            action=request.action,
            parameters=request.parameters
        )
        
        return SystemActionResponse(
            action=request.action,
            success=result["success"],
            message=result["message"],
            data=result.get("data")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"System action {request.action} failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System action failed: {str(e)}"
        )