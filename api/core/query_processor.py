"""
Query processing module.

Handles query execution through agent sessions with timeout and error handling.
"""

import logging
import threading
from contextlib import contextmanager
from typing import Optional

from api.core.models import QueryResponse
from api.core.sessions import SessionInfo
from api.middleware.error_handler import QueryTimeoutException
from api.routers.health import metrics

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Exception raised when query execution times out."""
    pass


@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for query timeout.
    
    Uses threading timer for timeout since we're in synchronous code.
    """
    timer = None
    timed_out = threading.Event()
    
    def timeout_handler():
        timed_out.set()
    
    try:
        if seconds > 0:
            timer = threading.Timer(seconds, timeout_handler)
            timer.start()
        yield timed_out
    finally:
        if timer:
            timer.cancel()


class QueryProcessor:
    """
    Processes queries through agent sessions.
    
    Handles query execution with timeout, error handling, and metrics collection.
    """
    
    @staticmethod
    def execute_query(
        session_info: SessionInfo,
        query: str,
        max_iterations: int,
        timeout_seconds: int
    ) -> QueryResponse:
        """
        Execute a query within a session.
        
        Args:
            session_info: Session information
            query: Natural language query
            max_iterations: Maximum React loop iterations
            timeout_seconds: Query timeout in seconds
            
        Returns:
            Query response with answer and metadata
            
        Raises:
            QueryTimeoutException: If query execution times out
            Exception: For other execution errors
        """
        logger.info(f"Executing query for session {session_info.session_id}: {query[:100]}...")
        
        # Use session lock to prevent concurrent queries
        if not session_info.lock.acquire(blocking=False):
            raise Exception("Another query is already in progress for this session")
        
        try:
            # Mark session as processing
            session_info.start_processing(query)
            
            # Execute with timeout
            with timeout_context(timeout_seconds) as timed_out:
                # Create a thread to run the query
                result = None
                error = None
                
                def run_query():
                    nonlocal result, error
                    try:
                        # Execute query through agent session with progress callback
                        result = session_info.agent_session.query(
                            text=query,
                            max_iterations=max_iterations,
                            progress_callback=session_info.add_progress_step
                        )
                    except Exception as e:
                        error = e
                
                # Start query in thread
                query_thread = threading.Thread(target=run_query)
                query_thread.start()
                
                # Wait for completion or timeout
                query_thread.join(timeout=timeout_seconds)
                
                # Check if timed out
                if timed_out.is_set() or query_thread.is_alive():
                    logger.error(f"Query timed out after {timeout_seconds} seconds")
                    session_info.finish_processing()
                    raise QueryTimeoutException(timeout_seconds)
                
                # Check for errors
                if error:
                    session_info.finish_processing()
                    raise error
                
                if not result:
                    session_info.finish_processing()
                    raise Exception("Query execution failed to produce a result")
                
                # Mark processing as complete
                session_info.finish_processing()
                
                # Update session
                session_info.touch()
                
                # Record metrics
                metrics.record_query(result.execution_time)
                
                # Build response
                return QueryResponse(
                    answer=result.answer,
                    execution_time=result.execution_time,
                    iterations=result.iterations,
                    tools_used=result.tools_used,
                    conversation_turn=result.conversation_turn,
                    had_context=result.had_context,
                    session_id=session_info.session_id
                )
                
        finally:
            session_info.lock.release()
    
    @staticmethod
    def validate_query(query: str) -> bool:
        """
        Validate a query before execution.
        
        Args:
            query: Query text to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation
        if not query or not query.strip():
            return False
        
        # Check length (handled by Pydantic model, but double-check)
        if len(query) > 2000:
            return False
        
        return True