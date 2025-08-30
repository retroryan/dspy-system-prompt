"""
Session management for the API.

Handles creation, storage, retrieval, and lifecycle of agent sessions.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

from agentic_loop.session import AgentSession
from api.core.models import SessionResponse, SessionConfig
from api.utils.config import config
from api.middleware.error_handler import (
    SessionNotFoundException,
    SessionExpiredException,
    ToolSetNotFoundException
)

logger = logging.getLogger(__name__)


class SessionInfo:
    """Container for session information and state."""
    
    def __init__(
        self,
        session_id: str,
        agent_session: AgentSession,
        tool_set: str,
        user_id: str
    ):
        self.session_id = session_id
        self.agent_session = agent_session
        self.tool_set = tool_set
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.status = "active"
        self.lock = threading.Lock()
    
    def touch(self):
        """Update last accessed time."""
        self.last_accessed = datetime.now()
    
    def is_expired(self, ttl_minutes: int) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_accessed + timedelta(minutes=ttl_minutes)
        return datetime.now() > expiry_time
    
    def to_response(self) -> SessionResponse:
        """Convert to response model."""
        return SessionResponse(
            session_id=self.session_id,
            tool_set=self.tool_set,
            user_id=self.user_id,
            created_at=self.created_at,
            status=self.status,
            conversation_turns=self.agent_session.conversation_turn
        )


class SessionManager:
    """
    Manages all active sessions.
    
    Provides thread-safe session operations with automatic cleanup.
    """
    
    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = True
        self._start_cleanup_task()
    
    def create_session(
        self,
        session_id: str,
        tool_set: str,
        user_id: str,
        session_config: Optional[SessionConfig] = None
    ) -> SessionInfo:
        """
        Create a new session with automatic cleanup.
        
        When a user reaches the maximum session limit (50), the oldest
        50 sessions are automatically deleted to make room for new sessions.
        
        Args:
            session_id: Unique session identifier
            tool_set: Tool set name
            user_id: User identifier
            session_config: Optional conversation history configuration
            
        Returns:
            Created session information
            
        Raises:
            ToolSetNotFoundException: If tool set is invalid
        """
        # Validate tool set
        valid_tool_sets = ["agriculture", "ecommerce", "events"]
        if tool_set not in valid_tool_sets:
            raise ToolSetNotFoundException(tool_set)
        
        with self.lock:
            # Check user session limit - exclude expired sessions
            user_sessions = [
                s for s in self.sessions.values()
                if s.user_id == user_id 
                and s.status == "active" 
                and not s.is_expired(config.session_ttl_minutes)
            ]
            
            # Auto-cleanup: Delete oldest sessions when reaching limit
            if len(user_sessions) >= config.max_sessions_per_user:
                # Sort sessions by creation time (oldest first)
                sorted_sessions = sorted(user_sessions, key=lambda s: s.created_at)
                
                # Delete the oldest 50 sessions (or all if less than 50)
                sessions_to_delete = sorted_sessions[:min(50, len(sorted_sessions))]
                
                for session in sessions_to_delete:
                    session.status = "terminated"
                    del self.sessions[session.session_id]
                    logger.info(f"Auto-cleanup: Deleted old session {session.session_id} for user {user_id}")
                
                logger.info(f"Auto-cleanup: Deleted {len(sessions_to_delete)} old sessions for user {user_id}")
            
            # Create agent session with configuration
            agent_config = None
            if session_config:
                agent_config = {
                    "max_messages": session_config.max_messages,
                    "summarize_removed": session_config.summarize_removed
                }
            
            try:
                agent_session = AgentSession(
                    tool_set_name=tool_set,
                    user_id=user_id,
                    config=agent_config,
                    verbose=config.debug_mode
                )
            except Exception as e:
                logger.error(f"Failed to create agent session: {str(e)}")
                raise
            
            # Create session info
            session_info = SessionInfo(
                session_id=session_id,
                agent_session=agent_session,
                tool_set=tool_set,
                user_id=user_id
            )
            
            # Store session
            self.sessions[session_id] = session_info
            
            logger.info(f"Created session {session_id} for user {user_id} with {tool_set} tools")
            return session_info
    
    def get_session(self, session_id: str) -> SessionInfo:
        """
        Get an active session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information
            
        Raises:
            SessionNotFoundException: If session doesn't exist
            SessionExpiredException: If session has expired
        """
        with self.lock:
            if session_id not in self.sessions:
                raise SessionNotFoundException(session_id)
            
            session = self.sessions[session_id]
            
            # Check if expired
            if session.is_expired(config.session_ttl_minutes):
                session.status = "expired"
                raise SessionExpiredException(session_id)
            
            # Update last accessed
            session.touch()
            return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.status = "terminated"
                del self.sessions[session_id]
                logger.info(f"Deleted session {session_id}")
                return True
            return False
    
    def reset_session(self, session_id: str) -> SessionInfo:
        """
        Reset a session's conversation history.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Reset session information
            
        Raises:
            SessionNotFoundException: If session doesn't exist
            SessionExpiredException: If session has expired
        """
        session = self.get_session(session_id)
        
        with session.lock:
            session.agent_session.reset()
            session.touch()
            logger.info(f"Reset session {session_id}")
            return session
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user's sessions
        """
        with self.lock:
            return [
                s for s in self.sessions.values()
                if s.user_id == user_id 
                and s.status == "active"
                and not s.is_expired(config.session_ttl_minutes)
            ]
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        with self.lock:
            return len([
                s for s in self.sessions.values() 
                if s.status == "active" and not s.is_expired(config.session_ttl_minutes)
            ])
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        with self.lock:
            expired_ids = []
            for session_id, session in self.sessions.items():
                if session.is_expired(config.session_ttl_minutes):
                    session.status = "expired"
                    expired_ids.append(session_id)
            
            for session_id in expired_ids:
                del self.sessions[session_id]
                logger.debug(f"Cleaned up expired session {session_id}")
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
    
    def _cleanup_task(self):
        """Background task for session cleanup."""
        while self.running:
            try:
                time.sleep(config.cleanup_interval_seconds)
                self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
    
    def _start_cleanup_task(self):
        """Start the background cleanup task."""
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_task,
            daemon=True
        )
        self.cleanup_thread.start()
        logger.debug("Started session cleanup task")
    
    def shutdown(self):
        """Shutdown the session manager."""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Session manager shut down")


# Global session manager instance
session_manager = SessionManager()