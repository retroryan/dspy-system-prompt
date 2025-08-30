"""
Demo execution system.

Manages demo workflow execution with real-time output capture
and status tracking.
"""

import uuid
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Optional, Iterator
from queue import Queue, Empty

from agentic_loop.session import AgentSession
from api.core.demo_models import (
    DemoType, DemoStatus, DemoOutputType, DemoOutputLine, DemoResponse
)

logger = logging.getLogger(__name__)


class DemoExecutor:
    """Manages demo execution and output capture."""
    
    def __init__(self):
        self._demos: Dict[str, 'DemoExecution'] = {}
        self._demos_lock = threading.RLock()  # Use RLock for recursive locking
        self._cleanup_thread = None
        self._running = True
        self._start_cleanup_thread()
    
    def start_demo(self, demo_type: DemoType, user_id: str, verbose: bool = True) -> str:
        """
        Start a demo execution.
        
        Args:
            demo_type: Type of demo to run
            user_id: User identifier  
            verbose: Enable verbose output
            
        Returns:
            Demo execution ID
        """
        demo_id = str(uuid.uuid4())
        
        # Get demo workflow
        workflow = self._get_demo_workflow(demo_type)
        if not workflow:
            raise ValueError(f"Unknown demo type: {demo_type}")
        
        # Get proper tool set for demo
        tool_set = self._get_demo_tool_set(demo_type)
        
        # Create demo execution
        demo_execution = DemoExecution(
            demo_id=demo_id,
            demo_type=demo_type,
            user_id=user_id,
            workflow=workflow,
            tool_set=tool_set,
            verbose=verbose
        )
        
        with self._demos_lock:
            self._demos[demo_id] = demo_execution
        
        # Start execution in background thread
        thread = threading.Thread(
            target=self._execute_demo,
            args=(demo_execution,),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started demo {demo_id} (type: {demo_type}, user: {user_id})")
        return demo_id
    
    def get_demo(self, demo_id: str) -> Optional[DemoResponse]:
        """Get demo information."""
        with self._demos_lock:
            demo = self._demos.get(demo_id)
            if not demo:
                return None
            return demo.to_response()
    
    def get_demo_output(self, demo_id: str, since_line: int = 0) -> Optional[List[DemoOutputLine]]:
        """Get demo output lines since specified line number."""
        with self._demos_lock:
            demo = self._demos.get(demo_id)
            if not demo:
                return None
            return demo.get_output_since(since_line)
    
    def cancel_demo(self, demo_id: str) -> bool:
        """Cancel a running demo."""
        with self._demos_lock:
            demo = self._demos.get(demo_id)
            if not demo:
                return False
            
            demo.cancel()
        logger.info(f"Cancelled demo {demo_id}")
        return True
    
    def list_demos(self, user_id: Optional[str] = None) -> List[DemoResponse]:
        """List all demos, optionally filtered by user."""
        demos = []
        with self._demos_lock:
            for demo in self._demos.values():
                if user_id is None or demo.user_id == user_id:
                    demos.append(demo.to_response())
        
        # Sort by start time, most recent first
        demos.sort(key=lambda d: d.started_at, reverse=True)
        return demos
    
    def cleanup_old_demos(self, max_age_hours: int = 24):
        """Remove old completed demos."""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        to_remove = []
        
        with self._demos_lock:
            for demo_id, demo in self._demos.items():
                if (demo.status in [DemoStatus.COMPLETED, DemoStatus.FAILED, DemoStatus.CANCELLED] and
                    demo.started_at.timestamp() < cutoff):
                    to_remove.append(demo_id)
            
            for demo_id in to_remove:
                del self._demos[demo_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old demos")
    
    def shutdown(self):
        """Shutdown the demo executor."""
        self._running = False
        
        # Cancel all running demos
        with self._demos_lock:
            for demo in self._demos.values():
                if demo.status == DemoStatus.RUNNING:
                    demo.cancel()
    
    def _get_demo_tool_set(self, demo_type: DemoType) -> str:
        """Get the appropriate tool set for a demo type."""
        tool_set_mapping = {
            DemoType.AGRICULTURE: "agriculture",
            DemoType.ECOMMERCE: "ecommerce",
            DemoType.WEATHER: "agriculture",  # Weather tools are in agriculture set
            DemoType.MEMORY: "ecommerce"  # Memory tools are in ecommerce set
        }
        return tool_set_mapping.get(demo_type, "agriculture")
    
    def _get_demo_workflow(self, demo_type: DemoType) -> Optional[List[str]]:
        """Get the query workflow for a demo type."""
        workflows = {
            DemoType.AGRICULTURE: [
                "What's the current weather in Des Moines, Iowa?",
                "How does that compare to the weather in Omaha, Nebraska?", 
                "What's the 7-day forecast for Des Moines?",
                "Based on the current weather and forecast, should I plant corn today in Des Moines?",
                "What about soil conditions - are they suitable for corn planting?",
                "Give me a final recommendation considering all the weather and soil information."
            ],
            DemoType.ECOMMERCE: [
                "Show me my recent orders",
                "What laptops are available under $1500?",
                "Add the best laptop to my cart",
                "What's currently in my shopping cart?",
                "Process checkout with my saved payment and address"
            ],
            DemoType.WEATHER: [
                "What's the weather in Tokyo?",
                "What's the weather in Paris?", 
                "Compare the weather between Tokyo and Paris"
            ],
            DemoType.MEMORY: [
                "My name is John and I live in Seattle",
                "What did I just tell you about myself?",
                "I work as a software engineer at a tech company",
                "What do you know about me now?",
                "Summarize everything I've told you"
            ]
        }
        return workflows.get(demo_type)
    
    def _execute_demo(self, demo_execution: 'DemoExecution'):
        """Execute a demo in the background."""
        try:
            demo_execution.execute()
        except Exception as e:
            logger.error(f"Demo execution failed: {str(e)}")
            demo_execution.fail(str(e))
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup_loop():
            while self._running:
                try:
                    time.sleep(300)  # Clean up every 5 minutes
                    self.cleanup_old_demos()
                except Exception as e:
                    logger.error(f"Cleanup thread error: {str(e)}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()


class DemoExecution:
    """Represents a single demo execution."""
    
    def __init__(self, demo_id: str, demo_type: DemoType, user_id: str, 
                 workflow: List[str], tool_set: str, verbose: bool = True):
        self.demo_id = demo_id
        self.demo_type = demo_type
        self.user_id = user_id
        self.workflow = workflow
        self.tool_set = tool_set
        self.verbose = verbose
        
        self.status = DemoStatus.PENDING
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.session_id: Optional[str] = None
        self.execution_time: Optional[float] = None
        self.total_queries = 0
        self.total_iterations = 0
        self.tools_used: List[str] = []
        self.error_message: Optional[str] = None
        
        self._output_lines: List[DemoOutputLine] = []
        self._cancelled = False
        self._lock = threading.Lock()
    
    def execute(self):
        """Execute the demo workflow."""
        with self._lock:
            if self.status != DemoStatus.PENDING:
                return
            self.status = DemoStatus.RUNNING
        
        start_time = time.time()
        
        try:
            self._add_output(DemoOutputType.INFO, f"Starting {self.demo_type.value} demo...")
            
            # Create session for demo
            from agentic_loop.session import AgentSession
            session = AgentSession(
                tool_set_name=self.tool_set,
                user_id=f"demo_{self.user_id}",
                verbose=self.verbose
            )
            
            self.session_id = session.session_id
            self._add_output(DemoOutputType.COMMAND, f"Created session: {self.session_id}")
            
            # Execute workflow
            all_tools_used = set()
            
            for i, query in enumerate(self.workflow, 1):
                if self._cancelled:
                    self._add_output(DemoOutputType.ERROR, "Demo cancelled by user")
                    with self._lock:
                        self.status = DemoStatus.CANCELLED
                    return
                
                self._add_output(
                    DemoOutputType.INFO,
                    f"Query {i}/{len(self.workflow)}: {query}"
                )
                
                # Execute query
                query_start = time.time()
                result = session.query(query)
                query_time = time.time() - query_start
                
                # Track metrics
                self.total_queries += 1
                self.total_iterations += result.iterations
                if result.tools_used:
                    all_tools_used.update(result.tools_used)
                
                # Add output
                self._add_output(
                    DemoOutputType.OUTPUT,
                    f"Result: {result.answer[:200]}{'...' if len(result.answer) > 200 else ''}",
                    metadata={
                        "execution_time": query_time,
                        "iterations": result.iterations,
                        "tools_used": result.tools_used
                    }
                )
                
                self._add_output(
                    DemoOutputType.METRICS,
                    f"Query {i} completed: {query_time:.1f}s, {result.iterations} iterations, tools: {result.tools_used or 'none'}"
                )
            
            self.tools_used = list(all_tools_used)
            self.execution_time = time.time() - start_time
            
            with self._lock:
                self.status = DemoStatus.COMPLETED
                self.completed_at = datetime.now()
            
            self._add_output(
                DemoOutputType.SUCCESS,
                f"✅ Demo completed successfully! Total time: {self.execution_time:.1f}s"
            )
            
        except Exception as e:
            self.error_message = str(e)
            with self._lock:
                self.status = DemoStatus.FAILED
                self.completed_at = datetime.now()
                
            self._add_output(DemoOutputType.ERROR, f"Demo failed: {str(e)}")
            logger.error(f"Demo {self.demo_id} failed: {str(e)}")
    
    def cancel(self):
        """Cancel the demo execution."""
        with self._lock:
            if self.status == DemoStatus.RUNNING:
                self._cancelled = True
    
    def fail(self, error: str):
        """Mark demo as failed."""
        with self._lock:
            self.status = DemoStatus.FAILED
            self.error_message = error
            self.completed_at = datetime.now()
    
    def get_output_since(self, line_number: int) -> List[DemoOutputLine]:
        """Get output lines since specified line number."""
        with self._lock:
            if line_number >= len(self._output_lines):
                return []
            return self._output_lines[line_number:]
    
    def to_response(self) -> DemoResponse:
        """Convert to response model."""
        with self._lock:
            return DemoResponse(
                demo_id=self.demo_id,
                demo_type=self.demo_type,
                user_id=self.user_id,
                status=self.status,
                started_at=self.started_at,
                completed_at=self.completed_at,
                session_id=self.session_id,
                execution_time=self.execution_time,
                total_queries=self.total_queries,
                total_iterations=self.total_iterations,
                tools_used=self.tools_used,
                error_message=self.error_message
            )
    
    def _add_output(self, output_type: DemoOutputType, text: str, metadata: Optional[Dict] = None):
        """Add an output line."""
        line = DemoOutputLine(
            type=output_type,
            text=text,
            metadata=metadata
        )
        
        with self._lock:
            self._output_lines.append(line)
        
        if self.verbose:
            logger.info(f"Demo {self.demo_id}: {text}")

