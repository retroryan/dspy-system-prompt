"""
Query execution endpoints.

Handles query processing through agent sessions.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from api.core.models import QueryRequest, QueryResponse
from api.core.sessions import session_manager
from api.core.query_processor import QueryProcessor
from api.utils.config import config
from api.middleware.error_handler import (
    SessionNotFoundException,
    SessionExpiredException,
    QueryTimeoutException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Queries"])


@router.post("/{session_id}/query", response_model=QueryResponse)
def execute_query(session_id: str, request: QueryRequest):
    """
    Execute a query within a session.
    
    Processes the query through the agentic loop using the session's
    configured tool set. The query is executed with conversation context
    from previous interactions in the session.
    
    Args:
        session_id: Session identifier
        request: Query parameters
        
    Returns:
        Query execution results including answer and metadata
        
    Raises:
        400: Invalid query
        404: Session not found
        408: Query execution timeout
        410: Session has expired
        500: Query execution error
    """
    try:
        # Validate query
        if not QueryProcessor.validate_query(request.query):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid query"
            )
        
        # Get session
        session_info = session_manager.get_session(session_id)
        
        logger.info(
            f"Processing query for session {session_id} "
            f"(user: {session_info.user_id}, turn: {session_info.agent_session.conversation_turn + 1})"
        )
        
        # Execute query
        response = QueryProcessor.execute_query(
            session_info=session_info,
            query=request.query,
            max_iterations=request.max_iterations,
            timeout_seconds=config.query_timeout_seconds
        )
        
        logger.info(
            f"Query completed for session {session_id}: "
            f"{response.iterations} iterations, {response.execution_time:.2f}s, "
            f"tools: {response.tools_used}"
        )
        
        return response
        
    except (SessionNotFoundException, SessionExpiredException, QueryTimeoutException) as e:
        # These exceptions are already properly formatted
        raise e
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Query execution failed for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )