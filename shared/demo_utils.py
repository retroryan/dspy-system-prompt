"""
Demo utility functions for enhanced clarity and educational value.

This module provides helper functions to make demos more clear, educational,
and visually appealing. It includes phase markers, concept highlights,
and structured logging for better understanding of the system's behavior.
"""

from typing import Optional, List, Dict, Any
import time
from datetime import datetime


class DemoLogger:
    """Rich logging for demo workflows with separate sections for each phase."""
    
    def __init__(self, demo_name: str, total_queries: int):
        self.demo_name = demo_name
        self.total_queries = total_queries
        self.query_number = 0
        self.start_time = time.time()
        self.iteration_start = None
        
    def log_query_start(self, query: str, context_count: int):
        """Log the start of a query with context information."""
        self.query_number += 1
        print(f"\n{'='*80}")
        print(f"Turn {self.query_number}/{self.total_queries}")
        print(f"{'='*80}")
        print(f"🗨️  Query: {query}")
        print(f"📚 Context: {context_count} previous interactions")
        if context_count > 0:
            print("💭 This query can build on previous conversation context")
        print()
    
    def log_react_start(self):
        """Log React loop start with clear section separator."""
        print(f"{'='*80}")
        print("Starting React loop")
        print(f"{'='*80}")
        self.iteration_start = time.time()
        self.react_call_count = 0
    
    def log_react_iteration(self, iteration: int, thought: str, tool_name: str, tool_args: Dict[str, Any], result: str):
        """Log individual React iteration results."""
        self.react_call_count += 1
        print(f"react loop call {self.react_call_count} - log of results:")
        print(f"  Thought: {thought}")
        if tool_name:
            print(f"  Tool: {tool_name}")
            print(f"  Args: {tool_args}")
            print(f"  Result: {result[:100]}{'...' if len(result) > 100 else ''}")
        else:
            print(f"  Action: Final Answer")
            print(f"  Result: {result[:100]}{'...' if len(result) > 100 else ''}")
        print()
    
    def log_react_complete(self, result):
        """Log React loop completion with summary."""
        execution_time = time.time() - self.iteration_start
        print(f"summary:")
        print(f"✓ React loop completed in {execution_time:.1f}s")
        print(f"  Total iterations: {result.iterations}")
        if result.tools_used:
            print(f"  Tools used: {', '.join(result.tools_used)}")
        else:
            print("  Tools used: None (used context)")
        print()
    
    def log_extract_start(self):
        """Log Extract agent start with clear section separator."""
        print(f"{'='*80}")
        print("Extract Agent")
        print(f"{'='*80}")
        
    def log_extract_complete(self, answer: str):
        """Log Extract agent completion with final answer."""
        print("log of call results:")
        print("✓ Answer extracted and synthesized")
        print()
        print("🎯 Final Result:")
        import textwrap
        wrapped = textwrap.fill(answer, width=70,
                               initial_indent="   ",
                               subsequent_indent="   ")
        print(wrapped)
        print()
    
    def log_conversation_stats(self, session):
        """Log conversation state and memory information."""
        print(f"📊 Conversation Stats:")
        print(f"  - Total interactions: {session.history.total_trajectories_processed}")
        print(f"  - Active trajectories: {len(session.history.trajectories)}")
        print(f"  - Memory summaries: {len(session.history.summaries)}")
        
        # Show memory management status
        if len(session.history.summaries) > 0:
            print(f"  - Memory window: Active (summaries created)")
        else:
            print(f"  - Memory window: All conversations retained")
        print()
    
    def log_demo_complete(self, session):
        """Log demo completion with comprehensive summary."""
        total_time = time.time() - self.start_time
        
        print(f"{'='*80}")
        print("📋 Final Demo Summary")
        print(f"{'='*80}")
        
        print(f"\n🎯 {self.demo_name} Workflow Complete!")
        print(f"⏱️  Total execution time: {total_time:.1f}s")
        print(f"🗨️  Queries processed: {self.query_number}")
        print(f"🧠 Memory state: {len(session.history.trajectories)} active, {len(session.history.summaries)} summarized")
        
        print(f"\n✅ Key Demonstrations:")
        print(f"  ✓ Context building across multiple queries")
        print(f"  ✓ Memory management and conversation continuity") 
        print(f"  ✓ Tool usage with context awareness")
        print(f"  ✓ Natural workflow progression")
        
        # Show conversation flow summary
        if len(session.history.trajectories) > 1:
            print(f"\n📜 Conversation Flow:")
            for i, traj in enumerate(session.history.trajectories, 1):
                query_preview = traj.user_query[:60] + "..." if len(traj.user_query) > 60 else traj.user_query
                print(f"  {i}. {query_preview}")


# Legacy static methods for backwards compatibility
class DemoLoggerLegacy:
    """Legacy static methods for backwards compatibility."""
    
    @staticmethod
    def phase(phase_name: str, description: str, width: int = 80) -> None:
        """Mark major demo phases clearly."""
        print(f"\n{'='*width}")
        print(f"🎯 DEMO PHASE: {phase_name}")
        print(f"📝 {description}")
        print(f"{'='*width}\n")
        time.sleep(0.5)
    
    @staticmethod
    def context_used(context_type: str, detail: str) -> None:
        """Show when and how context influences behavior."""
        print(f"🔗 Context [{context_type}]: {detail}")
    
    @staticmethod
    def tool_selection(tool_name: str, reason: Optional[str] = None) -> None:
        """Highlight tool selection decisions."""
        if reason:
            print(f"🔧 Tool Selected: {tool_name} - {reason}")
        else:
            print(f"🔧 Tool Selected: {tool_name}")
    
    @staticmethod
    def memory_event(event_type: str, detail: str) -> None:
        """Highlight memory management events."""
        print(f"💾 Memory Event [{event_type}]: {detail}")
    
    @staticmethod
    def section_header(title: str, char: str = '=', width: int = 60) -> None:
        """Create a section header for organization."""
        print(f"\n{char*width}")
        print(f"{title}")
        print(f"{char*width}")


def visualize_conversation_flow(
    trajectories: List[Any],
    summaries: List[Any],
    max_display: int = 5
) -> None:
    """
    Create ASCII visualization of conversation flow.
    
    Args:
        trajectories: List of trajectory objects
        summaries: List of summary objects
        max_display: Maximum number of trajectories to display
    """
    print("\n📊 Conversation Flow Visualization:")
    print("="*60)
    
    # Show summaries if present
    if summaries:
        print("\n📝 Summarized History:")
        for i, summary in enumerate(summaries, 1):
            print(f"  └─ Summary {i}: {summary.trajectory_count} trajectories")
            if hasattr(summary, 'tools_used') and summary.tools_used:
                print(f"      Tools: {', '.join(summary.tools_used[:3])}")
        print("")
    
    # Show trajectory timeline
    print("🔄 Active Trajectories:")
    display_trajectories = trajectories[-max_display:] if len(trajectories) > max_display else trajectories
    
    for i, traj in enumerate(display_trajectories):
        is_last = (i == len(display_trajectories) - 1)
        marker = "└──" if is_last else "├──"
        
        # Get query preview
        query = traj.user_query if hasattr(traj, 'user_query') else "Unknown query"
        query_preview = query[:40] + "..." if len(query) > 40 else query
        
        print(f"{marker} [{i+1}] {query_preview}")
        
        # Show tools used if available
        if hasattr(traj, 'tools_used') and traj.tools_used:
            tools = traj.tools_used[:3]
            tools_str = ', '.join(tools)
            if len(traj.tools_used) > 3:
                tools_str += f" (+{len(traj.tools_used)-3} more)"
            
            indent = "    " if is_last else "│   "
            print(f"{indent} Tools: {tools_str}")
        
        # Show metadata if available
        if hasattr(traj, 'metadata') and traj.metadata:
            indent = "    " if is_last else "│   "
            if 'conversation_turn' in traj.metadata:
                print(f"{indent} Turn: #{traj.metadata['conversation_turn']}")
    
    if len(trajectories) > max_display:
        print(f"\n  ... and {len(trajectories) - max_display} more trajectories")
    
    print("="*60)


def show_context_influence(
    query: str,
    context_available: bool,
    context_references: List[str]
) -> None:
    """
    Highlight how context influences query understanding.
    
    Args:
        query: The current query
        context_available: Whether context is available
        context_references: List of context-dependent words/phrases in the query
    """
    if not context_references:
        return
    
    print("\n🎭 Context Influence Analysis:")
    print(f"  Query: '{query}'")
    
    if context_available:
        print(f"  ✅ Context Available: Can resolve references")
        for ref in context_references:
            print(f"     • '{ref}' → will be resolved from context")
    else:
        print(f"  ⚠️  No Context: References may fail")
        for ref in context_references:
            print(f"     • '{ref}' → needs context to understand")
    print()


def format_performance_metrics(
    execution_time: float,
    iterations: int,
    tools_used: List[str],
    context_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Format performance metrics for display.
    
    Args:
        execution_time: Total execution time in seconds
        iterations: Number of React iterations
        tools_used: List of tools that were used
        context_size: Optional size of context in characters
    
    Returns:
        Formatted metrics dictionary
    """
    metrics = {
        "time": f"{execution_time:.2f}s",
        "iterations": iterations,
        "tools": len(tools_used)
    }
    
    if context_size is not None:
        metrics["context_size"] = f"{context_size:,} chars"
    
    return metrics



def highlight_summary_creation(
    trajectories_removed: int,
    summary_text: str,
    tools_preserved: List[str]
) -> None:
    """
    Highlight when summaries are created.
    
    Args:
        trajectories_removed: Number of trajectories being summarized
        summary_text: The created summary
        tools_preserved: Tools mentioned in the summary
    """
    print("\n🎯 SUMMARY CREATION EVENT")
    print("="*60)
    print(f"📝 Summarizing {trajectories_removed} trajectories:")
    print(f"   Summary: {summary_text[:150]}..." if len(summary_text) > 150 else f"   Summary: {summary_text}")
    if tools_preserved:
        print(f"   Preserved Tools: {', '.join(tools_preserved)}")
    print("="*60)
    print()


class DemoScenario:
    """Structured demo scenario for clear demonstration."""
    
    def __init__(
        self,
        name: str,
        description: str,
        queries: List[str],
        expected_behaviors: List[str],
        concepts_demonstrated: List[str]
    ):
        """
        Initialize a demo scenario.
        
        Args:
            name: Scenario name
            description: What this scenario demonstrates
            queries: List of queries to run
            expected_behaviors: List of expected behaviors
            concepts_demonstrated: List of concepts being shown
        """
        self.name = name
        self.description = description
        self.queries = queries
        self.expected_behaviors = expected_behaviors
        self.concepts_demonstrated = concepts_demonstrated
    
    def introduce(self) -> None:
        """Introduce the scenario to the user."""
        print(f"\n{'='*70}")
        print(f"📚 SCENARIO: {self.name}")
        print(f"{'='*70}")
        print(f"\n📝 Description: {self.description}")
        
        print("\n🎯 Concepts Demonstrated:")
        for concept in self.concepts_demonstrated:
            print(f"  • {concept}")
        
        print("\n✅ Expected Behaviors:")
        for behavior in self.expected_behaviors:
            print(f"  • {behavior}")
        
        print(f"\n📋 Queries to Run ({len(self.queries)} total):")
        for i, query in enumerate(self.queries, 1):
            print(f"  {i}. {query}")
        
        print(f"\n{'='*70}\n")
        time.sleep(1)  # Pause for reading