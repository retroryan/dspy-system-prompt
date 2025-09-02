"""
Demo execution endpoints.

Handles demo workflow execution, status tracking, and output streaming.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query, Depends
from api.core.demo_models import (
    DemoStartRequest, DemoResponse, DemoOutputResponse, DemoListResponse
)
from api.core.demo_executor import DemoExecutor
from api.core.dependencies import get_demo_executor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demos", tags=["Demos"])


@router.post("", response_model=DemoResponse, status_code=status.HTTP_201_CREATED)
def start_demo(
    request: DemoStartRequest,
    demo_executor: DemoExecutor = Depends(get_demo_executor)
):
    """
    Start a demo execution.
    
    Initiates a demo workflow execution with the specified type.
    The demo runs asynchronously and can be monitored via the status
    and output endpoints.
    
    Args:
        request: Demo start parameters
        
    Returns:
        Demo execution information
        
    Raises:
        400: Invalid demo type or parameters
        500: Demo start failure
    """
    try:
        demo_id = demo_executor.start_demo(
            demo_type=request.demo_type,
            user_id=request.user_id,
            verbose=request.verbose
        )
        
        # Get the created demo info
        demo = demo_executor.get_demo(demo_id)
        if not demo:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create demo execution"
            )
        
        logger.info(f"Started demo {demo_id} (type: {request.demo_type}, user: {request.user_id})")
        return demo
        
    except ValueError as e:
        logger.error(f"Invalid demo request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to start demo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start demo: {str(e)}"
        )


@router.get("/{demo_id}", response_model=DemoResponse)
def get_demo(
    demo_id: str,
    demo_executor: DemoExecutor = Depends(get_demo_executor)
):
    """
    Get demo execution status.
    
    Retrieves current status and metadata for a demo execution.
    
    Args:
        demo_id: Demo execution identifier
        
    Returns:
        Demo execution information
        
    Raises:
        404: Demo not found
    """
    demo = demo_executor.get_demo(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo {demo_id} not found"
        )
    
    return demo


@router.get("/{demo_id}/output", response_model=DemoOutputResponse)
def get_demo_output(
    demo_id: str,
    since_line: int = Query(default=0, ge=0, description="Get output since this line number"),
    demo_executor: DemoExecutor = Depends(get_demo_executor)
):
    """
    Get demo execution output.
    
    Retrieves output lines from a demo execution. Supports pagination
    via the since_line parameter for real-time streaming.
    
    Args:
        demo_id: Demo execution identifier
        since_line: Get output lines since this line number
        
    Returns:
        Demo output lines
        
    Raises:
        404: Demo not found
    """
    demo = demo_executor.get_demo(demo_id)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo {demo_id} not found"
        )
    
    output_lines = demo_executor.get_demo_output(demo_id, since_line)
    if output_lines is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo {demo_id} not found"
        )
    
    return DemoOutputResponse(
        demo_id=demo_id,
        output=output_lines,
        has_more=demo.status.value in ["pending", "running"],
        status=demo.status
    )


@router.delete("/{demo_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_demo(
    demo_id: str,
    demo_executor: DemoExecutor = Depends(get_demo_executor)
):
    """
    Cancel a running demo.
    
    Cancels a demo execution if it's currently running.
    Has no effect if the demo is already completed or failed.
    
    Args:
        demo_id: Demo execution identifier
        
    Raises:
        404: Demo not found
    """
    if not demo_executor.cancel_demo(demo_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demo {demo_id} not found"
        )
    
    logger.info(f"Cancelled demo {demo_id}")


@router.get("", response_model=DemoListResponse)
def list_demos(
    user_id: Optional[str] = Query(default=None, description="Filter by user ID"),
    limit: int = Query(default=50, le=100, description="Maximum number of demos to return"),
    demo_executor: DemoExecutor = Depends(get_demo_executor)
):
    """
    List demo executions.
    
    Retrieves a list of demo executions, optionally filtered by user.
    Results are sorted by start time, most recent first.
    
    Args:
        user_id: Optional user ID filter
        limit: Maximum number of results
        
    Returns:
        List of demo executions
    """
    demos = demo_executor.list_demos(user_id)
    
    # Apply limit
    if limit > 0:
        demos = demos[:limit]
    
    return DemoListResponse(
        demos=demos,
        total=len(demos)
    )