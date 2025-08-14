"""
Tests for ConversationHistory class.

This module tests the conversation history management functionality,
including trajectory management, sliding window, summary creation,
and context generation.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from shared.conversation_history import ConversationHistory
from shared.conversation_models import ConversationHistoryConfig, ConversationSummary
from shared.trajectory_models import Trajectory, TrajectoryStep, ToolStatus


def create_test_trajectory(query: str, tool_set: str = "test", num_steps: int = 3) -> Trajectory:
    """Helper function to create a test trajectory with steps."""
    trajectory = Trajectory(
        user_query=query,
        tool_set_name=tool_set,
        metadata={"test": "data"}
    )
    
    # Add some steps
    for i in range(num_steps):
        trajectory.add_step(
            thought=f"Thinking step {i+1}",
            tool_name=f"tool_{i}" if i < num_steps - 1 else "finish",
            tool_args={"arg": f"value_{i}"}
        )
        
        # Add observation for non-finish tools
        if i < num_steps - 1:
            trajectory.add_observation(
                tool_name=f"tool_{i}",
                status=ToolStatus.SUCCESS,
                result=f"Result from tool_{i}",
                execution_time_ms=100.0
            )
    
    trajectory.completed_at = datetime.now()
    return trajectory


class TestConversationHistory:
    """Tests for ConversationHistory class."""
    
    def test_initialization_default_config(self):
        """Test initialization with default configuration."""
        history = ConversationHistory()
        
        assert history.config.max_trajectories == 10
        assert history.config.summarize_removed == True
        assert len(history.trajectories) == 0
        assert len(history.summaries) == 0
        assert history.total_trajectories_processed == 0
    
    def test_initialization_custom_config(self):
        """Test initialization with custom configuration."""
        config = ConversationHistoryConfig(
            max_trajectories=5,
            summarize_removed=False,
            preserve_first_trajectories=1,
            preserve_last_trajectories=2
        )
        history = ConversationHistory(config)
        
        assert history.config.max_trajectories == 5
        assert history.config.summarize_removed == False
        assert history.config.preserve_first_trajectories == 1
        assert history.config.preserve_last_trajectories == 2
    
    def test_add_trajectory_basic(self):
        """Test adding trajectories to history."""
        history = ConversationHistory()
        
        # Add first trajectory
        traj1 = create_test_trajectory("Query 1")
        history.add_trajectory(traj1)
        
        assert len(history.trajectories) == 1
        assert history.trajectories[0] == traj1
        assert history.total_trajectories_processed == 1
        
        # Add second trajectory
        traj2 = create_test_trajectory("Query 2")
        history.add_trajectory(traj2)
        
        assert len(history.trajectories) == 2
        assert history.trajectories[1] == traj2
        assert history.total_trajectories_processed == 2
    
    def test_trajectory_window_not_triggered(self):
        """Test that window is not applied when under max_trajectories."""
        config = ConversationHistoryConfig(
            max_trajectories=5,
            preserve_first_trajectories=1,
            preserve_last_trajectories=3
        )
        history = ConversationHistory(config)
        
        # Add 4 trajectories (under limit of 5)
        for i in range(4):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        assert len(history.trajectories) == 4
        assert len(history.summaries) == 0
        assert history.total_trajectories_processed == 4
    
    @patch('shared.conversation_history.ReactExtract')
    def test_trajectory_window_triggered_with_summary(self, mock_extract_class):
        """Test window management with summary creation."""
        # Mock the Extract agent
        mock_extract = Mock()
        mock_extract.return_value = Mock(summary="Summary of removed trajectories")
        mock_extract_class.return_value = mock_extract
        
        config = ConversationHistoryConfig(
            max_trajectories=3,
            summarize_removed=True,
            preserve_first_trajectories=1,
            preserve_last_trajectories=1
        )
        history = ConversationHistory(config)
        
        # Add 4 trajectories to trigger window
        trajectories = []
        for i in range(4):
            traj = create_test_trajectory(f"Query {i}")
            trajectories.append(traj)
            history.add_trajectory(traj)
        
        # Should keep first 1 and last 1 (total 2 out of 3 max)
        assert len(history.trajectories) == 2
        assert history.trajectories[0].user_query == "Query 0"  # First preserved
        assert history.trajectories[1].user_query == "Query 3"  # Last preserved
        
        # Should have created a summary
        assert len(history.summaries) == 1
        assert history.summaries[0].trajectory_count == 2  # Removed Query 1 and 2
        assert history.summaries[0].summary_text == "Summary of removed trajectories"
    
    def test_trajectory_window_without_summary(self):
        """Test window management without summary creation."""
        config = ConversationHistoryConfig(
            max_trajectories=3,
            summarize_removed=False,  # No summaries
            preserve_first_trajectories=1,
            preserve_last_trajectories=1
        )
        history = ConversationHistory(config)
        
        # Add 4 trajectories
        for i in range(4):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        # Should still apply window
        assert len(history.trajectories) == 2
        # But no summaries created
        assert len(history.summaries) == 0
    
    @patch('shared.conversation_history.ReactExtract')
    def test_summary_creation_with_tools(self, mock_extract_class):
        """Test that summary includes tool usage information."""
        mock_extract = Mock()
        mock_extract.return_value = Mock(summary="Test summary")
        mock_extract_class.return_value = mock_extract
        
        history = ConversationHistory()
        
        # Create trajectory with specific tools
        traj = create_test_trajectory("Test query", num_steps=3)
        
        # Test _create_summary directly
        summary = history._create_summary([traj])
        
        assert summary.trajectory_count == 1
        assert summary.total_steps == 3
        assert "tool_0" in summary.tools_used
        assert "tool_1" in summary.tools_used
        assert "finish" not in summary.tools_used  # finish is excluded
    
    def test_summary_creation_fallback(self):
        """Test fallback summary when Extract agent fails."""
        with patch('shared.conversation_history.ReactExtract') as mock_extract_class:
            # Make Extract agent raise an exception
            mock_extract_class.side_effect = Exception("Extract failed")
            
            history = ConversationHistory()
            trajectories = [
                create_test_trajectory("Query 1"),
                create_test_trajectory("Query 2"),
                create_test_trajectory("Query 3")
            ]
            
            summary = history._create_summary(trajectories)
            
            # Should use fallback summary
            assert "Summarized 3 interactions" in summary.summary_text
            assert "Query 1, Query 2, Query 3" in summary.summary_text
    
    def test_get_context_for_agent(self):
        """Test context generation for agents."""
        history = ConversationHistory()
        
        # Add some trajectories
        for i in range(3):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        context = history.get_context_for_agent()
        
        assert context["trajectory_count"] == 3
        assert context["total_processed"] == 3
        assert len(context["trajectories"]) == 3
        assert context["has_summaries"] == False
        assert len(context["summaries"]) == 0
    
    @patch('shared.conversation_history.ReactExtract')
    def test_get_context_with_summaries(self, mock_extract_class):
        """Test context generation when summaries exist."""
        mock_extract = Mock()
        mock_extract.return_value = Mock(summary="Test summary")
        mock_extract_class.return_value = mock_extract
        
        config = ConversationHistoryConfig(
            max_trajectories=2,
            preserve_first_trajectories=0,
            preserve_last_trajectories=2
        )
        history = ConversationHistory(config)
        
        # Add 3 trajectories to trigger summary
        for i in range(3):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        context = history.get_context_for_agent()
        
        assert context["has_summaries"] == True
        assert len(context["summaries"]) == 1
        assert "summary_info" in context
        assert context["summary_info"]["total_summarized_trajectories"] == 1
    
    def test_build_context_prompt_empty(self):
        """Test context prompt generation with empty history."""
        history = ConversationHistory()
        prompt = history.build_context_prompt()
        
        assert prompt == "No previous conversation history."
    
    def test_build_context_prompt_with_trajectories(self):
        """Test context prompt generation with trajectories."""
        history = ConversationHistory()
        
        # Add trajectories
        history.add_trajectory(create_test_trajectory("What's the weather?"))
        history.add_trajectory(create_test_trajectory("How about tomorrow?"))
        
        prompt = history.build_context_prompt()
        
        assert "Recent Interactions:" in prompt
        assert "What's the weather?" in prompt
        assert "How about tomorrow?" in prompt
        assert "tool_0, tool_1" in prompt  # Should list tools used
    
    def test_get_full_history_text(self):
        """Test full history text generation."""
        history = ConversationHistory()
        
        # Add some trajectories
        for i in range(2):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        text = history.get_full_history_text()
        
        assert "=== ACTIVE CONVERSATION ===" in text
        assert "Query 0" in text
        assert "Query 1" in text
        assert "=== STATISTICS ===" in text
        assert "Total Interactions Processed: 2" in text
    
    def test_clear_history(self):
        """Test clearing conversation history."""
        history = ConversationHistory()
        
        # Add trajectories
        for i in range(3):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        # Clear all
        history.clear_history()
        
        assert len(history.trajectories) == 0
        assert len(history.summaries) == 0
        assert history.total_trajectories_processed == 0
    
    def test_clear_history_keep_last(self):
        """Test clearing history while keeping recent trajectories."""
        history = ConversationHistory()
        
        # Add trajectories
        for i in range(5):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        # Keep last 2
        history.clear_history(keep_last=2)
        
        assert len(history.trajectories) == 2
        assert history.trajectories[0].user_query == "Query 3"
        assert history.trajectories[1].user_query == "Query 4"
        assert history.total_trajectories_processed == 2
    
    def test_format_trajectories_for_summary(self):
        """Test trajectory formatting for summary creation."""
        history = ConversationHistory()
        
        trajectories = [
            create_test_trajectory("Query 1", num_steps=2),
            create_test_trajectory("Query 2", num_steps=3)
        ]
        
        formatted = history._format_trajectories_for_summary(trajectories)
        
        assert "Interaction 1:" in formatted
        assert "User Query: Query 1" in formatted
        assert "Tools Used: tool_0" in formatted
        assert "Interaction 2:" in formatted
        assert "User Query: Query 2" in formatted
    
    def test_preservation_logic(self):
        """Test complex preservation logic with first and last trajectories."""
        config = ConversationHistoryConfig(
            max_trajectories=5,
            preserve_first_trajectories=2,
            preserve_last_trajectories=2
        )
        history = ConversationHistory(config)
        
        # Add 7 trajectories
        for i in range(7):
            history.add_trajectory(create_test_trajectory(f"Query {i}"))
        
        # Window triggers when adding 6th (exceeds max of 5), removes middle trajectories
        # Keeps: [0, 1, 4, 5], then adds 7th -> [0, 1, 4, 5, 6] = 5 trajectories total
        assert len(history.trajectories) == 5
        assert history.trajectories[0].user_query == "Query 0"
        assert history.trajectories[1].user_query == "Query 1"
        assert history.trajectories[2].user_query == "Query 4"
        assert history.trajectories[3].user_query == "Query 5"
        assert history.trajectories[4].user_query == "Query 6"