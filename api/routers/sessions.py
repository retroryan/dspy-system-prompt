"""
Session-related endpoints.

Handles session creation, retrieval, deletion, and reset operations.
"""

import uuid
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from api.core.models import (
    SessionCreateRequest,
    SessionResponse,
    ErrorResponse
)
from api.core.sessions import session_manager
from api.middleware.error_handler import (
    SessionNotFoundException,
    SessionExpiredException,
    MaxSessionsExceededException,
    ToolSetNotFoundException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(request: SessionCreateRequest):
    """
    Create a new agent session.
    
    Creates a session with the specified tool set and configuration.
    Sessions expire after the configured TTL (default 30 minutes).
    
    Args:
        request: Session creation parameters
        
    Returns:
        Created session information
        
    Raises:
        400: Invalid tool set or configuration
        429: User has reached maximum session limit
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        session_info = session_manager.create_session(
            session_id=session_id,
            tool_set=request.tool_set,
            user_id=request.user_id,
            session_config=request.config
        )
        
        logger.info(f"Created session {session_id} for user {request.user_id}")
        return session_info.to_response()
        
    except (ToolSetNotFoundException, MaxSessionsExceededException) as e:
        # These exceptions are already properly formatted
        raise e
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str):
    """
    Get session information.
    
    Retrieves information about an active session including its status
    and conversation turn count.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session information
        
    Raises:
        404: Session not found
        410: Session has expired
    """
    try:
        session_info = session_manager.get_session(session_id)
        return session_info.to_response()
    except (SessionNotFoundException, SessionExpiredException) as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str):
    """
    Delete a session.
    
    Terminates and removes a session immediately.
    
    Args:
        session_id: Session identifier
        
    Raises:
        404: Session not found
    """
    if not session_manager.delete_session(session_id):
        raise SessionNotFoundException(session_id)
    
    logger.info(f"Deleted session {session_id}")


@router.post("/{session_id}/reset", response_model=SessionResponse)
def reset_session(session_id: str):
    """
    Reset a session's conversation history.
    
    Clears the conversation history while keeping the session active.
    Useful for starting a new conversation without creating a new session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Reset session information
        
    Raises:
        404: Session not found
        410: Session has expired
    """
    try:
        session_info = session_manager.reset_session(session_id)
        return session_info.to_response()
    except (SessionNotFoundException, SessionExpiredException) as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to reset session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset session: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[SessionResponse])
def get_user_sessions(user_id: str):
    """
    Get all active sessions for a user.
    
    Returns a list of all active sessions belonging to the specified user.
    
    Args:
        user_id: User identifier
        
    Returns:
        List of user's active sessions
    """
    try:
        sessions = session_manager.get_user_sessions(user_id)
        return [session.to_response() for session in sessions]
    except Exception as e:
        logger.error(f"Failed to get sessions for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user sessions: {str(e)}"
        )