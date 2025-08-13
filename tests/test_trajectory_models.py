"""
Tests for the Pydantic trajectory models.

This module tests the type-safe trajectory system to ensure all models
work correctly and maintain data integrity.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from shared.trajectory_models import (
    ToolStatus,
    ThoughtStep,
    ToolInvocation,
    ToolObservation,
    TrajectoryStep,
    Trajectory,
    ExtractResult
)


class TestThoughtStep:
    """Tests for ThoughtStep model."""
    
    def test_thought_creation(self):
        """Test creating a thought step."""
        thought = ThoughtStep(content="I need to check the weather")
        assert thought.content == "I need to check the weather"
    
    def test_thought_immutable(self):
        """Test that thought steps are immutable."""
        thought = ThoughtStep(content="Initial thought")
        with pytest.raises(ValidationError):
            thought.content = "Modified thought"


class TestToolInvocation:
    """Tests for ToolInvocation model."""
    
    def test_tool_invocation_creation(self):
        """Test creating a tool invocation."""
        invocation = ToolInvocation(
            tool_name="get_weather",
            tool_args={"location": "Seattle"}
        )
        assert invocation.tool_name == "get_weather"
        assert invocation.tool_args == {"location": "Seattle"}
    
    def test_finish_tool_invocation(self):
        """Test creating a finish tool invocation."""
        invocation = ToolInvocation(
            tool_name="finish",
            tool_args={}
        )
        assert invocation.tool_name == "finish"
        assert invocation.tool_args == {}


class TestToolObservation:
    """Tests for ToolObservation model."""
    
    def test_successful_observation(self):
        """Test creating a successful tool observation."""
        obs = ToolObservation(
            tool_name="get_weather",
            status=ToolStatus.SUCCESS,
            result="Sunny, 72°F",
            execution_time_ms=150.5
        )
        assert obs.status == ToolStatus.SUCCESS
        assert obs.result == "Sunny, 72°F"
        assert obs.error is None
        assert obs.execution_time_ms == 150.5
    
    def test_error_observation(self):
        """Test creating an error observation."""
        obs = ToolObservation(
            tool_name="get_weather",
            status=ToolStatus.ERROR,
            error="API rate limit exceeded",
            execution_time_ms=50.0
        )
        assert obs.status == ToolStatus.ERROR
        assert obs.error == "API rate limit exceeded"
        assert obs.result is None


class TestTrajectoryStep:
    """Tests for TrajectoryStep model."""
    
    def test_regular_step(self):
        """Test creating a regular trajectory step."""
        step = TrajectoryStep(
            iteration=1,
            thought=ThoughtStep(content="Checking weather"),
            tool_invocation=ToolInvocation(
                tool_name="get_weather",
                tool_args={"location": "Seattle"}
            )
        )
        assert step.iteration == 1
        assert not step.is_finish
        assert not step.has_error
    
    def test_finish_step(self):
        """Test creating a finish step."""
        step = TrajectoryStep(
            iteration=2,
            thought=ThoughtStep(content="I have all the information needed"),
            tool_invocation=ToolInvocation(
                tool_name="finish",
                tool_args={}
            )
        )
        assert step.is_finish
        assert not step.has_error
    
    def test_error_step(self):
        """Test a step with an error observation."""
        step = TrajectoryStep(
            iteration=1,
            thought=ThoughtStep(content="Checking weather"),
            tool_invocation=ToolInvocation(
                tool_name="get_weather",
                tool_args={"location": "Seattle"}
            ),
            observation=ToolObservation(
                tool_name="get_weather",
                status=ToolStatus.ERROR,
                error="API error",
                execution_time_ms=100
            )
        )
        assert step.has_error
        assert not step.is_finish


class TestTrajectory:
    """Tests for Trajectory model."""
    
    def test_trajectory_creation(self):
        """Test creating a trajectory."""
        trajectory = Trajectory(
            user_query="What's the weather in Seattle?",
            tool_set_name="agriculture"
        )
        assert trajectory.user_query == "What's the weather in Seattle?"
        assert trajectory.tool_set_name == "agriculture"
        assert trajectory.iteration_count == 0
        assert not trajectory.is_complete
        assert trajectory.max_iterations == 5
        assert isinstance(trajectory.started_at, datetime)
    
    def test_adding_steps(self):
        """Test adding steps to trajectory."""
        trajectory = Trajectory(
            user_query="What's the weather?",
            tool_set_name="agriculture"
        )
        
        # Add first step
        step1 = trajectory.add_step(
            thought="I need to check the weather",
            tool_name="get_weather",
            tool_args={"location": "Seattle"}
        )
        
        assert trajectory.iteration_count == 1
        assert step1.iteration == 1
        assert not step1.is_finish
        
        # Add observation
        trajectory.add_observation(
            tool_name="get_weather",
            status=ToolStatus.SUCCESS,
            result="Sunny, 72°F",
            execution_time_ms=150
        )
        
        assert trajectory.last_observation.status == ToolStatus.SUCCESS
        assert trajectory.last_observation.result == "Sunny, 72°F"
        
        # Add finish step
        step2 = trajectory.add_step(
            thought="I have the weather information",
            tool_name="finish",
            tool_args={}
        )
        
        assert step2.is_finish
        assert trajectory.is_complete
        assert trajectory.iteration_count == 2
    
    def test_tools_used(self):
        """Test getting list of tools used."""
        trajectory = Trajectory(
            user_query="Check weather and forecast",
            tool_set_name="agriculture"
        )
        
        # Add weather check
        trajectory.add_step(
            thought="Checking current weather",
            tool_name="get_weather",
            tool_args={"location": "Seattle"}
        )
        trajectory.add_observation(
            tool_name="get_weather",
            status=ToolStatus.SUCCESS,
            result="Sunny",
            execution_time_ms=100
        )
        
        # Add forecast check
        trajectory.add_step(
            thought="Checking forecast",
            tool_name="get_forecast",
            tool_args={"location": "Seattle"}
        )
        trajectory.add_observation(
            tool_name="get_forecast",
            status=ToolStatus.SUCCESS,
            result="Partly cloudy",
            execution_time_ms=200
        )
        
        # Add finish
        trajectory.add_step(
            thought="Got all information",
            tool_name="finish",
            tool_args={}
        )
        
        # Verify tools_used excludes finish
        assert trajectory.tools_used == ["get_weather", "get_forecast"]
        assert "finish" not in trajectory.tools_used
    
    def test_total_execution_time(self):
        """Test calculating total execution time."""
        trajectory = Trajectory(
            user_query="Test query",
            tool_set_name="test"
        )
        
        # Add steps with observations
        trajectory.add_step("Step 1", "tool1", {})
        trajectory.add_observation("tool1", ToolStatus.SUCCESS, "Result 1", execution_time_ms=100)
        
        trajectory.add_step("Step 2", "tool2", {})
        trajectory.add_observation("tool2", ToolStatus.SUCCESS, "Result 2", execution_time_ms=150)
        
        assert trajectory.total_execution_time_ms == 250
    
    def test_max_iterations(self):
        """Test that trajectory is complete at max iterations."""
        trajectory = Trajectory(
            user_query="Test",
            tool_set_name="test",
            max_iterations=2
        )
        
        # Add max iterations without finish
        trajectory.add_step("Step 1", "tool1", {})
        trajectory.add_step("Step 2", "tool2", {})
        
        assert trajectory.iteration_count == 2
        assert trajectory.is_complete  # Complete due to max iterations
        assert not trajectory.steps[-1].is_finish
    
    def test_llm_format(self):
        """Test formatting trajectory for LLM."""
        trajectory = Trajectory(
            user_query="What's the weather?",
            tool_set_name="agriculture"
        )
        
        trajectory.add_step(
            thought="Checking weather",
            tool_name="get_weather",
            tool_args={"location": "Seattle"}
        )
        trajectory.add_observation(
            tool_name="get_weather",
            status=ToolStatus.SUCCESS,
            result="Sunny, 72°F",
            execution_time_ms=100
        )
        
        trajectory.add_step(
            thought="I have the information",
            tool_name="finish",
            tool_args={}
        )
        
        formatted = trajectory.to_llm_format()
        assert "User Query: What's the weather?" in formatted
        assert "Iteration 1:" in formatted
        assert "Thought: Checking weather" in formatted
        assert "Tool: get_weather" in formatted
        assert "Result: Sunny, 72°F" in formatted
        assert "Iteration 2:" in formatted
        assert "Tool: finish" in formatted
        assert "Status: Task complete" in formatted


class TestExtractResult:
    """Tests for ExtractResult model."""
    
    def test_extract_result_creation(self):
        """Test creating an extract result."""
        result = ExtractResult(
            answer="The weather in Seattle is sunny and 72°F",
            reasoning="Based on the weather API response"
        )
        assert result.answer == "The weather in Seattle is sunny and 72°F"
        assert result.reasoning == "Based on the weather API response"
    
    def test_extract_result_default_reasoning(self):
        """Test extract result with default reasoning."""
        result = ExtractResult(
            answer="The weather is sunny"
        )
        assert result.answer == "The weather is sunny"
        assert result.reasoning == ""
    
    def test_extract_result_immutable(self):
        """Test that extract results are immutable."""
        result = ExtractResult(
            answer="Initial answer",
            reasoning="Initial reasoning"
        )
        with pytest.raises(ValidationError):
            result.answer = "Modified answer"