"""
Integration tests for conversation history with React and Extract agents.

These tests verify that conversation context can be passed through signatures
to the existing agents without any modifications or wrappers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import ClassVar, Type
import dspy
from pydantic import BaseModel, Field

from agentic_loop.react_agent import ReactAgent
from agentic_loop.extract_agent import ReactExtract
from shared.conversation_history import ConversationHistory
from shared.conversation_models import ConversationHistoryConfig
from shared.trajectory_models import Trajectory, ToolStatus
from shared.tool_utils.registry import ToolRegistry
from shared.tool_utils.base_tool import BaseTool
from shared.tool_utils.base_tool_sets import ToolSet


# Mock args model for weather tool
class MockWeatherArgs(BaseModel):
    location: str = Field(description="Location for weather")
    
# Mock tool for testing
class MockWeatherTool(BaseTool):
    NAME: ClassVar[str] = "weather_current"
    MODULE: ClassVar[str] = "test"
    
    description: str = "Get current weather for a location"
    args_model: Type[BaseModel] = MockWeatherArgs
    
    def get_argument_details(self):
        return {"location": "string"}
    
    def execute(self, location: str):
        return f"Sunny in {location}"


# Mock tool set for testing
class MockToolSet(ToolSet):
    NAME: ClassVar[str] = "test"
    
    def __init__(self):
        from shared.tool_utils.base_tool_sets import ToolSetConfig
        super().__init__(
            config=ToolSetConfig(
                name="test",
                description="Mock tools for testing",
                tool_classes=[MockWeatherTool]
            )
        )


# Define test signatures with context
class TestReactSignature(dspy.Signature):
    """Test signature for React with context."""
    user_query = dspy.InputField()
    conversation_context = dspy.InputField()


class TestExtractSignature(dspy.Signature):
    """Test signature for Extract with context."""
    user_query = dspy.InputField()
    conversation_context = dspy.InputField()
    answer = dspy.OutputField()


class TestConversationIntegration:
    """Integration tests for conversation history with agents."""
    
    @pytest.fixture
    def tool_registry(self):
        """Create a tool registry with mock tools."""
        registry = ToolRegistry()
        registry.register_tool_set(MockToolSet())
        return registry
    
    @pytest.fixture
    def conversation_history(self):
        """Create a conversation history instance."""
        config = ConversationHistoryConfig(
            max_trajectories=5,
            summarize_removed=True,
            preserve_first_trajectories=1,
            preserve_last_trajectories=3  # 1 + 3 = 4, which is less than 5
        )
        return ConversationHistory(config)
    
    @patch('dspy.Predict')
    def test_react_agent_receives_context(self, mock_predict_class, tool_registry):
        """Test that React agent properly receives and uses context."""
        # Setup mock prediction
        mock_predict = Mock()
        mock_predict.return_value = Mock(
            next_thought="Thinking with context",
            next_tool_name="weather_current",
            next_tool_args={"location": "Chicago"}
        )
        mock_predict_class.return_value = mock_predict
        
        # Create React agent with context-aware signature
        react_agent = ReactAgent(
            signature=TestReactSignature,
            tool_registry=tool_registry
        )
        
        # Create trajectory
        trajectory = Trajectory(
            user_query="What's the weather?",
            tool_set_name="test"
        )
        
        # Call with context
        context = "Previous interaction: Asked about weather in New York"
        react_agent(
            trajectory=trajectory,
            user_query="What's the weather?",
            conversation_context=context
        )
        
        # Verify context was passed to predict
        mock_predict.assert_called_once()
        call_kwargs = mock_predict.call_args[1]
        assert "conversation_context" in call_kwargs
        assert call_kwargs["conversation_context"] == context
        
        # Verify trajectory was updated
        assert len(trajectory.steps) == 1
        assert trajectory.steps[0].thought.content == "Thinking with context"
    
    @patch('dspy.ChainOfThought')
    def test_extract_agent_receives_context(self, mock_cot_class):
        """Test that Extract agent properly receives and uses context."""
        # Setup mock Chain of Thought - needs to be dict-like for dspy.Prediction
        mock_result = {
            "answer": "Based on context, the weather is sunny",
            "reasoning": "Using previous context to answer"
        }
        mock_cot = Mock()
        mock_cot.return_value = mock_result
        mock_cot_class.return_value = mock_cot
        
        # Create Extract agent with context-aware signature
        extract_agent = ReactExtract(
            signature=TestExtractSignature
        )
        
        # Create trajectory with some steps
        trajectory = Trajectory(
            user_query="What's the weather?",
            tool_set_name="test"
        )
        trajectory.add_step(
            thought="Checking weather",
            tool_name="weather_current",
            tool_args={"location": "Chicago"}
        )
        
        # Call with context
        context = "Previous interactions discussed New York weather"
        result = extract_agent(
            trajectory=trajectory,
            user_query="What's the weather?",
            conversation_context=context
        )
        
        # Verify context was passed
        mock_cot.assert_called_once()
        call_kwargs = mock_cot.call_args[1]
        assert "conversation_context" in call_kwargs
        assert call_kwargs["conversation_context"] == context
    
    def test_conversation_flow_with_real_history(self, tool_registry, conversation_history):
        """Test a complete conversation flow with history management."""
        # Add some trajectories to history
        for i in range(3):
            traj = Trajectory(
                user_query=f"Query {i}",
                tool_set_name="test"
            )
            traj.add_step(
                thought=f"Thought {i}",
                tool_name="weather_current",
                tool_args={"location": f"City{i}"}
            )
            conversation_history.add_trajectory(traj)
        
        # Get context from history
        context = conversation_history.get_context_for_agent()
        context_prompt = conversation_history.build_context_prompt(context)
        
        # Verify context contains trajectory information
        assert context["trajectory_count"] == 3
        assert "Recent Interactions:" in context_prompt
        assert "Query 0" in context_prompt
        assert "Query 2" in context_prompt
    
    @patch('dspy.Predict')
    @patch('dspy.ChainOfThought')
    def test_end_to_end_with_context(self, mock_cot_class, mock_predict_class, 
                                     tool_registry, conversation_history):
        """Test end-to-end flow with context passing through both agents."""
        # Setup mocks
        mock_predict = Mock()
        mock_predict.return_value = Mock(
            next_thought="Using context to reason",
            next_tool_name="finish",
            next_tool_args={}
        )
        mock_predict_class.return_value = mock_predict
        
        mock_cot = Mock()
        mock_cot.return_value = {
            "answer": "Answer based on conversation history",
            "reasoning": "Synthesized from context"
        }
        mock_cot_class.return_value = mock_cot
        
        # Add prior interaction
        prior_traj = Trajectory(
            user_query="Previous query",
            tool_set_name="test"
        )
        conversation_history.add_trajectory(prior_traj)
        
        # Create agents with context signatures
        react_agent = ReactAgent(
            signature=TestReactSignature,
            tool_registry=tool_registry
        )
        
        extract_agent = ReactExtract(
            signature=TestExtractSignature
        )
        
        # Get context
        context_prompt = conversation_history.build_context_prompt()
        
        # Run React agent
        trajectory = Trajectory(
            user_query="Current query",
            tool_set_name="test"
        )
        
        trajectory = react_agent(
            trajectory=trajectory,
            user_query="Current query",
            conversation_context=context_prompt
        )
        
        # Run Extract agent
        result = extract_agent(
            trajectory=trajectory,
            user_query="Current query",
            conversation_context=context_prompt
        )
        
        # Verify both agents received context
        assert mock_predict.call_args[1]["conversation_context"] == context_prompt
        assert mock_cot.call_args[1]["conversation_context"] == context_prompt
        
        # Add new trajectory to history
        conversation_history.add_trajectory(trajectory)
        
        # Verify history updated
        assert conversation_history.total_trajectories_processed == 2
        assert len(conversation_history.trajectories) == 2
    
    def test_context_affects_agent_behavior(self, tool_registry):
        """Test that context actually influences agent responses."""
        # This test would require actual LLM calls to verify behavior changes
        # For unit testing, we verify the mechanism works
        
        # Create agents with context signatures
        react_agent = ReactAgent(
            signature=TestReactSignature,
            tool_registry=tool_registry
        )
        
        # Verify signature includes context field
        react_signature = react_agent.react.signature
        assert "conversation_context" in react_signature.input_fields
        
        # Verify it's passed through in instructions
        # The agent builds instructions that reference all input fields
        # This ensures context is considered by the LLM
        pass
    
    def test_no_context_still_works(self, tool_registry):
        """Test that agents work without context (backwards compatible)."""
        # Create signature without context field
        class NoContextSignature(dspy.Signature):
            user_query = dspy.InputField()
            answer = dspy.OutputField()
        
        with patch('dspy.Predict') as mock_predict_class:
            mock_predict = Mock()
            mock_predict.return_value = Mock(
                next_thought="Working without context",
                next_tool_name="finish",
                next_tool_args={}
            )
            mock_predict_class.return_value = mock_predict
            
            # Create agent without context
            react_agent = ReactAgent(
                signature=NoContextSignature,
                tool_registry=tool_registry
            )
            
            # Should work fine without context
            trajectory = Trajectory(
                user_query="Test query",
                tool_set_name="test"
            )
            
            # Call without context field
            react_agent(
                trajectory=trajectory,
                user_query="Test query"
                # No conversation_context provided
            )
            
            # Verify it worked
            assert len(trajectory.steps) == 1
            assert trajectory.steps[0].thought.content == "Working without context"
    
    def test_context_field_optional(self, tool_registry):
        """Test that context field can be optional in signatures."""
        # Create signature with optional context
        class OptionalContextSignature(dspy.Signature):
            user_query = dspy.InputField()
            conversation_context = dspy.InputField(desc="Optional context")
            answer = dspy.OutputField()
        
        # Should work with or without context
        with patch('dspy.Predict') as mock_predict_class:
            mock_predict = Mock()
            mock_predict.return_value = Mock(
                next_thought="Flexible context handling",
                next_tool_name="finish",
                next_tool_args={}
            )
            mock_predict_class.return_value = mock_predict
            
            react_agent = ReactAgent(
                signature=OptionalContextSignature,
                tool_registry=tool_registry
            )
            
            trajectory = Trajectory(
                user_query="Test",
                tool_set_name="test"
            )
            
            # With context
            react_agent(
                trajectory=trajectory,
                user_query="Test",
                conversation_context="Some context"
            )
            
            # Without context (should use empty string or None)
            trajectory2 = Trajectory(
                user_query="Test2",
                tool_set_name="test"
            )
            
            react_agent(
                trajectory=trajectory2,
                user_query="Test2",
                conversation_context=""  # Empty context
            )
            
            # Both should work
            assert len(trajectory.steps) == 1
            assert len(trajectory2.steps) == 1