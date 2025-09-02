"""
Base classes for tool sets.

This module defines the core infrastructure for organizing tools into logical groups (tool sets).
Each tool set can contain multiple tools and provides a way to manage and load
collections of tools relevant to specific domains or functionalities.
"""
from typing import List, Optional, Dict, Type, ClassVar, Any
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr
import dspy

from .base_tool import ToolTestCase, BaseTool


class ToolSetTestCase(ToolTestCase):
    """
    Extends the base ToolTestCase to include tool set-specific metadata.

    This allows test cases to be associated with a particular tool set and
    optionally a scenario within that set, aiding in more organized testing.
    """
    tool_set: str  # The name of the tool set this test case belongs to
    scenario: Optional[str] = None  # An optional, more granular grouping for test cases within a tool set
    expected_arguments: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Expected arguments for each tool. Key is tool name, value is dict of arguments."
    )


class ToolSetConfig(BaseModel):
    """
    Configuration model for a ToolSet.

    This model defines the immutable properties of a tool set, such as its name,
    description, and the list of tool classes it contains.
    """
    model_config = ConfigDict(frozen=True)  # Ensures the configuration is immutable after creation
    
    name: str  # The unique name of the tool set (e.g., "agriculture", "ecommerce", "events")
    description: str  # A brief description of the tool set's purpose
    tool_classes: List[Type[BaseTool]]  # A list of direct references to the BaseTool subclasses included in this set


class ToolSet(BaseModel):
    """
    Base class for defining a collection of related tools.

    Subclasses should define their specific tools and provide test cases relevant
    to their domain. Tool sets can also provide custom DSPy signatures for React
    and Extract agents.
    """
    config: ToolSetConfig  # The immutable configuration for this tool set
    _initialized: bool = PrivateAttr(default=False)  # Track if initialization has been called
    
    def initialize(self) -> None:
        """
        Initialize the tool set when it's registered.
        
        This method is called once when the tool set is registered with the ToolRegistry.
        Subclasses can override this to perform one-time setup like:
        - Loading test data into databases
        - Setting up connections
        - Initializing shared resources
        
        The base implementation sets the _initialized flag to prevent duplicate initialization.
        """
        if not self._initialized:
            self._perform_initialization()
            self._initialized = True
    
    def _perform_initialization(self) -> None:
        """
        Protected method for actual initialization logic.
        
        Subclasses should override this method to implement their specific
        initialization requirements. This method is only called once per tool set instance.
        """
        # Default implementation does nothing
        # Subclasses override this for custom initialization
        pass
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Abstract method to be implemented by subclasses.

        Subclasses should return a list of `ToolSetTestCase` objects that are
        specific to the functionality provided by the tools within that set.

        Returns:
            List[ToolSetTestCase]: A list of test cases for the tool set.
        """
        return []
    
    @classmethod
    def get_react_signature(cls) -> Optional[Type[dspy.Signature]]:
        """
        Return the React signature for this tool set.
        
        The React signature contains domain-specific requirements for tool execution,
        such as coordinate extraction instructions or precision requirements.
        
        Returns:
            Optional[Type[dspy.Signature]]: The React signature class, or None to use default behavior
        """
        return None
    
    @classmethod
    def get_extract_signature(cls) -> Optional[Type[dspy.Signature]]:
        """
        Return the Extract signature for this tool set.
        
        The Extract signature contains domain input/output fields for final synthesis,
        without any tool-specific instructions.
        
        Returns:
            Optional[Type[dspy.Signature]]: The Extract signature class, or None to use default behavior
        """
        return None
    
    def provides_instances(self) -> bool:
        """
        Indicate whether this tool set provides instances directly.
        
        Instance-based tool sets (like MCP) should override this to return True.
        Class-based tool sets (default) return False.
        
        Returns:
            bool: True if tool set provides instances, False if it provides classes
        """
        return False
    
    def get_tool_instances(self) -> List[BaseTool]:
        """
        Return tool instances for instance-based tool sets.
        
        This method is called when provides_instances() returns True.
        Instance-based tool sets should override this to return their tool instances.
        
        Returns:
            List[BaseTool]: List of tool instances, empty for class-based tool sets
        """
        return []