"""
Unified base class for tools using Pydantic with built-in metadata.

This module defines the foundational classes for creating tools that can be
registered and used within the DSPy framework for multi-tool selection.
It leverages Pydantic for robust argument validation and clear data modeling.
"""
import logging
from typing import List, ClassVar, Type, Any, Dict, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

# Avoid circular imports
if TYPE_CHECKING:
    from agentic_loop.session import AgentSession

logger = logging.getLogger(__name__)


class ToolArgument(BaseModel):
    """
    Represents a single argument for a tool.

    This model is used to define the expected inputs for a tool, including
    its name, type, description, and whether it's required.
    """
    name: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")  # Valid Python identifier for the argument name
    type: str = Field(..., description="Python type name (e.g., 'str', 'int', 'float', 'bool', 'List[str]')")
    description: str = Field(..., min_length=1)  # A clear description of what the argument represents
    required: bool = Field(default=True)  # Whether the argument is mandatory
    default: Optional[Any] = None  # Default value if the argument is optional


class BaseTool(BaseModel, ABC):
    """
    Abstract base class for all tools in the system.

    Tools inherit from this class to provide a unified interface for definition,
    argument validation, and execution. It integrates with Pydantic for data
    modeling and validation.
    """
    
    # Class-level constants (not Pydantic fields) that must be defined by each concrete tool
    NAME: ClassVar[str]  # The unique name of the tool (e.g., "search_products")
    MODULE: ClassVar[str]  # The module/category the tool belongs to (e.g., "ecommerce", "productivity")
    
    # Session awareness flag - tools that need user context should set this to True
    _accepts_session: ClassVar[bool] = False
    
    # Instance fields that define the tool's characteristics
    description: str = Field(..., min_length=1)  # A brief explanation of what the tool does
    arguments: List[ToolArgument] = Field(default_factory=list)  # List of arguments the tool accepts
    
    # Required: Pydantic model for argument validation.
    # All tools must define this model to specify their expected arguments.
    args_model: Type[BaseModel] = Field(..., exclude=True)
    
    def __init_subclass__(cls, **kwargs):
        """
        Validates that subclasses of BaseTool define the required class variables (NAME, MODULE).
        Also ensures that the NAME is a valid Python identifier.
        """
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'NAME'):
            raise TypeError(f"{cls.__name__} must define a 'NAME' class variable.")
        if not hasattr(cls, 'MODULE'):
            raise TypeError(f"{cls.__name__} must define a 'MODULE' class variable.")
        # Validate NAME is a valid Python identifier to ensure it can be used programmatically
        if not cls.NAME.isidentifier():
            raise ValueError(f"{cls.__name__}.NAME must be a valid Python identifier, got: '{cls.NAME}'.")
    
    @property
    def name(self) -> str:
        """
        Returns the unique name of the tool, derived from the class-level NAME constant.
        """
        return self.NAME
    
    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic hook called after model initialization.
        Auto-populates the 'arguments' list from 'args_model'.
        """
        # Extract arguments from the required args_model
        if self.args_model:
            self.arguments = self._extract_arguments_from_model(self.args_model)
    
    @classmethod
    def _extract_arguments_from_model(cls, model: Type[BaseModel]) -> List[ToolArgument]:
        """
        Extracts a list of ToolArgument objects from a Pydantic BaseModel's schema.
        This allows tools to define their arguments using a Pydantic model for convenience.
        """
        schema = model.model_json_schema()  # Get the JSON schema of the Pydantic model
        properties = schema.get('properties', {})  # Extract properties (fields)
        required = schema.get('required', [])  # Get list of required fields
        
        arguments = []
        for field_name, field_info in properties.items():
            arguments.append(ToolArgument(
                name=field_name,
                type=field_info.get('type', 'string'),  # Default to 'string' if type is not specified
                description=field_info.get('description', ''),
                required=field_name in required,
                default=field_info.get('default')
            ))
        return arguments
    
    def get_argument_list(self) -> List[str]:
        """
        Returns a list of argument names for this tool.
        
        Returns:
            List of argument names as strings.
        """
        return [arg.name for arg in self.arguments]
    
    def get_argument_details(self) -> List[Dict[str, Any]]:
        """
        Returns detailed information about each argument.
        
        Returns:
            List of dictionaries containing argument details.
        """
        return [
            {
                "name": arg.name,
                "type": arg.type,
                "description": arg.description,
                "required": arg.required,
                "default": arg.default
            }
            for arg in self.arguments
        ]
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool's logic with the provided arguments.
        
        Tools that need user context should:
        1. Set _accepts_session = True as a class variable
        2. Access session from kwargs: session = kwargs.pop('session', None)
        3. Return error if session is required but missing

        Args:
            **kwargs: The arguments required for the tool's execution.
                     May include 'session' for session-aware tools.

        Returns:
            The result of the tool's operation (dict, str, or any JSON-serializable type).
        """
        raise NotImplementedError("Tool must implement execute()")
    
    def validate_and_execute(self, **kwargs) -> Any:
        """
        Validates the input arguments using the tool's 'args_model'
        and then executes the tool's logic.
        
        Session is passed through without validation if present,
        as it's not part of the args_model.
        
        Returns:
            The result of the tool's operation.
        """
        # Extract session before validation (not part of args_model)
        session = kwargs.pop('session', None)
        
        # Log what we're about to validate (truncate long args for security)
        args_str = str(kwargs)
        if len(args_str) > 500:
            args_str = args_str[:500] + "... (truncated)"
        logger.info(f"Tool '{self.name}': Validating arguments: {args_str}")
        logger.info(f"Tool '{self.name}': Expected args model: {self.args_model.__name__ if hasattr(self.args_model, '__name__') else type(self.args_model).__name__}")
        
        try:
            # Validate arguments using the Pydantic model
            validated_args = self.args_model(**kwargs)
            logger.info(f"Tool '{self.name}': Validation successful")
        except Exception as e:
            logger.error(
                f"Tool '{self.name}': Validation failed\n"
                f"Args received: {kwargs}\n"
                f"Error: {e}\n"
                f"Expected schema: {self.args_model.model_json_schema() if hasattr(self.args_model, 'model_json_schema') else 'N/A'}"
            )
            raise
        
        # Add session back if this tool accepts it
        execution_args = validated_args.model_dump()
        if self._accepts_session and session is not None:
            execution_args['session'] = session
            logger.info(f"Tool '{self.name}': Added session to execution args")
            
        # Execute the tool with the validated arguments  
        # Only log number of args at INFO level for security
        logger.info(f"Tool '{self.name}': Executing with {len(execution_args)} arguments")
        logger.debug(f"Tool '{self.name}': Execution args: {execution_args}")
        return self.execute(**execution_args)


class ToolTestCase(BaseModel):
    """
    Represents a single test case for evaluating tool selection.

    Used to define a user request and the expected tools that should be selected
    in response to that request.
    """
    request: str  # The user's natural language request
    expected_tools: List[str]  # A list of tool names expected to be selected
    description: str  # A brief description of the test case