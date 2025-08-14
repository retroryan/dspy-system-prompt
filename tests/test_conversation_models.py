"""
Tests for conversation history models.

This module tests the ConversationSummary and ConversationHistoryConfig models,
as well as the metadata field added to the Trajectory model.
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from shared.conversation_models import ConversationSummary, ConversationHistoryConfig
from shared.trajectory_models import Trajectory


class TestConversationSummary:
    """Tests for ConversationSummary model."""
    
    def test_create_valid_summary(self):
        """Test creating a valid conversation summary."""
        summary = ConversationSummary(
            trajectory_count=3,
            total_steps=15,
            tools_used=["weather_current", "weather_forecast"],
            summary_text="Discussed weather patterns in Iowa and Nebraska"
        )
        
        assert summary.trajectory_count == 3
        assert summary.total_steps == 15
        assert len(summary.tools_used) == 2
        assert "weather_current" in summary.tools_used
        assert summary.summary_text == "Discussed weather patterns in Iowa and Nebraska"
        assert isinstance(summary.created_at, datetime)
    
    def test_summary_immutability(self):
        """Test that ConversationSummary is immutable (frozen)."""
        summary = ConversationSummary(
            trajectory_count=1,
            total_steps=5,
            summary_text="Test summary"
        )
        
        with pytest.raises(Exception):  # Pydantic will raise validation error
            summary.trajectory_count = 2
    
    def test_summary_validation(self):
        """Test validation rules for ConversationSummary."""
        # trajectory_count must be >= 1
        with pytest.raises(ValueError):
            ConversationSummary(
                trajectory_count=0,
                total_steps=5,
                summary_text="Test"
            )
        
        # summary_text must not be empty
        with pytest.raises(ValueError):
            ConversationSummary(
                trajectory_count=1,
                total_steps=5,
                summary_text=""
            )
    
    def test_summary_with_empty_tools(self):
        """Test creating summary with no tools used."""
        summary = ConversationSummary(
            trajectory_count=1,
            total_steps=3,
            tools_used=[],
            summary_text="Simple conversation without tool usage"
        )
        
        assert summary.tools_used == []
        assert summary.trajectory_count == 1


class TestConversationHistoryConfig:
    """Tests for ConversationHistoryConfig model."""
    
    def test_create_default_config(self):
        """Test creating config with default values."""
        config = ConversationHistoryConfig()
        
        assert config.max_trajectories == 10
        assert config.summarize_removed == True
        assert config.preserve_first_trajectories == 1
        assert config.preserve_last_trajectories == 7
    
    def test_create_custom_config(self):
        """Test creating config with custom values."""
        config = ConversationHistoryConfig(
            max_trajectories=20,
            summarize_removed=False,
            preserve_first_trajectories=2,
            preserve_last_trajectories=10
        )
        
        assert config.max_trajectories == 20
        assert config.summarize_removed == False
        assert config.preserve_first_trajectories == 2
        assert config.preserve_last_trajectories == 10
    
    def test_config_immutability(self):
        """Test that ConversationHistoryConfig is immutable (frozen)."""
        config = ConversationHistoryConfig()
        
        with pytest.raises(Exception):  # Pydantic will raise validation error
            config.max_trajectories = 15
    
    def test_config_validation_bounds(self):
        """Test validation bounds for config values."""
        # max_trajectories must be >= 1
        with pytest.raises(ValueError):
            ConversationHistoryConfig(max_trajectories=0)
        
        # max_trajectories must be <= 100
        with pytest.raises(ValueError):
            ConversationHistoryConfig(max_trajectories=101)
        
        # preserve_last_trajectories must be >= 1
        with pytest.raises(ValueError):
            ConversationHistoryConfig(preserve_last_trajectories=0)
    
    def test_config_preservation_validation(self):
        """Test that preservation settings don't exceed max_trajectories."""
        # This should raise an error because preserve_first + preserve_last > max_trajectories
        with pytest.raises(ValueError, match="cannot exceed max_trajectories"):
            ConversationHistoryConfig(
                max_trajectories=5,
                preserve_first_trajectories=3,
                preserve_last_trajectories=3
            )
    
    def test_config_valid_preservation_edge_case(self):
        """Test valid edge case where preservation equals max_trajectories."""
        # This should be valid: 2 + 3 = 5
        config = ConversationHistoryConfig(
            max_trajectories=5,
            preserve_first_trajectories=2,
            preserve_last_trajectories=3
        )
        
        assert config.max_trajectories == 5
        assert config.preserve_first_trajectories == 2
        assert config.preserve_last_trajectories == 3


class TestTrajectoryMetadata:
    """Tests for the metadata field added to Trajectory model."""
    
    def test_create_trajectory_without_metadata(self):
        """Test creating trajectory without metadata (backward compatibility)."""
        trajectory = Trajectory(
            user_query="What's the weather?",
            tool_set_name="agriculture"
        )
        
        assert trajectory.metadata is None
        assert trajectory.user_query == "What's the weather?"
        assert trajectory.tool_set_name == "agriculture"
    
    def test_create_trajectory_with_metadata(self):
        """Test creating trajectory with metadata."""
        metadata = {
            "conversation_context": {
                "previous_interactions": 3,
                "total_interactions": 5,
                "has_summaries": True
            }
        }
        
        trajectory = Trajectory(
            user_query="What's the weather?",
            tool_set_name="agriculture",
            metadata=metadata
        )
        
        assert trajectory.metadata is not None
        assert trajectory.metadata["conversation_context"]["previous_interactions"] == 3
        assert trajectory.metadata["conversation_context"]["total_interactions"] == 5
        assert trajectory.metadata["conversation_context"]["has_summaries"] == True
    
    def test_metadata_flexibility(self):
        """Test that metadata can store various types of data."""
        metadata: Dict[str, Any] = {
            "string_value": "test",
            "number_value": 42,
            "list_value": [1, 2, 3],
            "dict_value": {"nested": "data"},
            "bool_value": True
        }
        
        trajectory = Trajectory(
            user_query="Test query",
            tool_set_name="test",
            metadata=metadata
        )
        
        assert trajectory.metadata["string_value"] == "test"
        assert trajectory.metadata["number_value"] == 42
        assert trajectory.metadata["list_value"] == [1, 2, 3]
        assert trajectory.metadata["dict_value"]["nested"] == "data"
        assert trajectory.metadata["bool_value"] == True
    
    def test_metadata_modification(self):
        """Test that metadata can be modified after creation."""
        trajectory = Trajectory(
            user_query="Test query",
            tool_set_name="test",
            metadata={"initial": "value"}
        )
        
        # Metadata dict should be mutable even though model is not frozen
        trajectory.metadata["new_key"] = "new_value"
        assert trajectory.metadata["new_key"] == "new_value"
        assert trajectory.metadata["initial"] == "value"
    
    def test_trajectory_existing_functionality(self):
        """Test that existing Trajectory functionality still works with metadata field."""
        trajectory = Trajectory(
            user_query="Test query",
            tool_set_name="test",
            max_iterations=10,
            metadata={"test": "data"}
        )
        
        # Test existing properties
        assert trajectory.is_complete == False
        assert trajectory.iteration_count == 0
        assert trajectory.last_observation is None
        assert trajectory.tools_used == []
        assert trajectory.total_execution_time_ms == 0
        
        # Test adding a step
        step = trajectory.add_step(
            thought="Testing",
            tool_name="test_tool",
            tool_args={"arg": "value"}
        )
        
        assert trajectory.iteration_count == 1
        assert len(trajectory.steps) == 1
        assert trajectory.steps[0].thought.content == "Testing"