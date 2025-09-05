"""Central registry for all tools adapted for agentic loop integration."""
import logging
import time
from typing import Dict, Type, Callable, List, Optional, Any, TYPE_CHECKING
import dspy
from ..models import ToolExecutionResult, ToolCall
from .base_tool import BaseTool
from .base_tool_sets import ToolSet, ToolSetTestCase

# Avoid circular imports
if TYPE_CHECKING:
    from agentic_loop.session import AgentSession

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    A central registry for managing and accessing all available tools in the system.

    This class provides methods to register new tool classes, retrieve tool instances
    by name, execute tools with given arguments, and manage test cases associated
    with registered tools. It ensures that tool names are unique and provides a
    single point of access for tool management.
    
    Updated for agentic loop integration to return ToolExecutionResult objects.
    """
    
    def __init__(self):
        """Initializes the ToolRegistry with empty dictionaries for tools and instances."""
        self._tools: Dict[str, Type[BaseTool]] = {}  # Stores tool classes, keyed by tool name
        self._instances: Dict[str, BaseTool] = {}  # Stores instantiated tool objects, keyed by tool name
        self._tool_set: Optional[ToolSet] = None  # Stores the current tool set if loaded
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Retrieves a tool instance by its name.

        Args:
            name (str): The name of the tool to retrieve.

        Returns:
            Optional[BaseTool]: The tool instance if found, otherwise None.
        """
        return self._instances.get(name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        Retrieves all registered tool instances.

        Returns:
            Dict[str, BaseTool]: A dictionary of all registered tool instances, keyed by their names.
        """
        return self._instances.copy()
    
    def get_tool_names(self) -> List[str]:
        """
        Retrieves a list of names of all registered tools.

        Returns:
            List[str]: A list containing the names of all registered tools.
        """
        return list(self._tools.keys())
    
    def execute_tool(self, tool_call: ToolCall) -> ToolExecutionResult:
        """
        Executes a registered tool by ToolCall and returns ToolExecutionResult.

        Args:
            tool_call (ToolCall): The tool call containing tool name and arguments.

        Returns:
            ToolExecutionResult: The result of the tool's execution with metadata.
        """
        start_time = time.time()
        
        try:
            tool = self.get_tool(tool_call.tool_name)
            if not tool:
                return ToolExecutionResult(
                    tool_name=tool_call.tool_name,
                    success=False,
                    result=None,
                    error=f"Unknown tool: {tool_call.tool_name}",
                    execution_time=time.time() - start_time,
                    parameters=tool_call.arguments
                )
            
            # Use the tool's validate_and_execute method for argument validation and execution
            result = tool.validate_and_execute(**tool_call.arguments)
            
            return ToolExecutionResult(
                tool_name=tool_call.tool_name,
                success=True,
                result=result,
                error=None,
                execution_time=time.time() - start_time,
                parameters=tool_call.arguments
            )
            
        except Exception as e:
            return ToolExecutionResult(
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time=time.time() - start_time,
                parameters=tool_call.arguments
            )
    
    def execute_tool_with_session(
        self,
        tool_name: str,
        session: Optional['AgentSession'] = None,
        **kwargs
    ) -> Any:
        """
        Execute a tool with session context injection.
        
        This method handles session injection for tools that need user context,
        following the strands pattern of passing context through invocation_state.
        
        Args:
            tool_name: Name of the tool to execute
            session: The agent session containing user context
            **kwargs: Tool arguments
            
        Returns:
            The result of the tool execution
        """
        # Truncate args for security in logs
        args_str = str(kwargs)
        if len(args_str) > 500:
            args_str = args_str[:500] + "... (truncated)"
        logger.info(f"Registry: Executing tool '{tool_name}' with {len(kwargs)} arguments")
        logger.debug(f"Registry: Tool arguments: {args_str}")
        
        tool = self.get_tool(tool_name)
        if not tool:
            logger.error(f"Registry: Unknown tool: {tool_name}")
            return {"error": f"Unknown tool: {tool_name}"}
        
        # Add session to kwargs if tool accepts it
        if hasattr(tool, '_accepts_session') and tool._accepts_session and session:
            logger.info(f"Registry: Adding session to tool '{tool_name}'")
            kwargs['session'] = session
        
        # Use validate_and_execute which handles session properly
        logger.debug(f"Registry: Calling validate_and_execute for '{tool_name}'" )
        return tool.validate_and_execute(**kwargs)
    
    def register_tool_set(self, tool_set: ToolSet) -> None:
        """
        Registers all tools from a tool set and initializes the tool set.
        
        Supports both class-based tool sets (original) and instance-based
        tool sets (for dynamic discovery like MCP).
        
        Args:
            tool_set: The tool set to register
        """
        self._tool_set = tool_set
        
        # Initialize the tool set (e.g., load test data, setup connections)
        tool_set.initialize()
        
        # Check if tool set provides instances directly (dynamic tools)
        if hasattr(tool_set, 'provides_instances') and tool_set.provides_instances():
            # Instance-based registration (for MCP and other dynamic tools)
            instances = tool_set.get_tool_instances()
            for instance in instances:
                tool_name = instance.name
                
                if tool_name in self._instances:
                    raise ValueError(f"Tool '{tool_name}' is already registered.")
                
                # Store instance directly
                self._instances[tool_name] = instance
                # Also store in _tools for compatibility (using instance's class)
                self._tools[tool_name] = instance.__class__
        else:
            # Class-based registration (original behavior)
            for tool_class in tool_set.config.tool_classes:
                tool_name = tool_class.NAME

                if tool_name in self._tools:
                    raise ValueError(f"Tool '{tool_name}' is already registered.")

                self._tools[tool_name] = tool_class

                # Create and cache tool instance. Tools are Pydantic models.
                instance = tool_class()
                self._instances[tool_name] = instance
    
    def get_all_test_cases(self) -> List[ToolSetTestCase]:
        """
        Returns test cases from the registered tool set.
        
        Returns:
            List[ToolSetTestCase]: Test cases from the tool set, or empty list if no tool set.
        """
        if self._tool_set:
            return self._tool_set.__class__.get_test_cases()
        return []
    
    def clear(self) -> None:
        """
        Clears all registered tools and their instances from the registry.

        This is primarily useful for testing scenarios to ensure a clean state.
        """
        self._tools.clear()
        self._instances.clear()
        self._tool_set = None
    
    def get_react_signature(self) -> Optional[Type[dspy.Signature]]:
        """
        Get the React signature from the current tool set.
        
        Returns:
            Optional[Type[dspy.Signature]]: The React signature class, or None if no tool set or default behavior
        """
        if self._tool_set:
            return self._tool_set.get_react_signature()
        return None
    
    def get_extract_signature(self) -> Optional[Type[dspy.Signature]]:
        """
        Get the Extract signature from the current tool set.
        
        Returns:
            Optional[Type[dspy.Signature]]: The Extract signature class, or None if no tool set or default behavior
        """
        if self._tool_set:
            return self._tool_set.get_extract_signature()
        return None