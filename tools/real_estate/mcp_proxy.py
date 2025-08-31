"""MCP Tool Proxy for DSPy integration without DSPy dependency.

This module provides a proxy that makes MCP tools compatible with the BaseTool interface
using instance-based approach inspired by DSPy's architecture.
"""
import asyncio
import logging
from typing import Any, Dict, ClassVar, Type, Optional, Callable
from pydantic import BaseModel, Field, create_model

from shared.tool_utils.base_tool import BaseTool, ToolArgument
from .mcp_client import MCPClient, MCPToolInfo

logger = logging.getLogger(__name__)


class MCPToolProxy(BaseTool):
    """Proxy that makes any MCP tool compatible with BaseTool interface.
    
    Uses closure pattern to capture MCP client session, inspired by DSPy's
    convert_mcp_tool() implementation.
    """
    
    MODULE: ClassVar[str] = "real_estate"
    NAME: ClassVar[str] = "mcp_proxy"  # Will be overridden per instance
    
    # Instance-specific fields (stored as private attributes, not Pydantic fields)
    # These are set in __init__ and stored using __dict__ to avoid Pydantic validation
    
    def __init__(self, mcp_tool_info: MCPToolInfo, mcp_client: MCPClient):
        """Create proxy for a specific MCP tool.
        
        Args:
            mcp_tool_info: Information about the MCP tool
            mcp_client: MCP client for executing tools
        """
        # Override class NAME with instance-specific name
        self.__class__.NAME = mcp_tool_info.name
        
        # Create args model from MCP schema
        args_model = self._create_args_model(mcp_tool_info)
        
        # Initialize base with description and args
        super().__init__(
            description=mcp_tool_info.description,
            args_model=args_model
        )
        
        # Store instance-specific data directly in __dict__ after initialization
        # This bypasses Pydantic validation for these internal attributes
        self.__dict__['_instance_name'] = mcp_tool_info.name
        self.__dict__['_mcp_tool_info'] = mcp_tool_info
        self.__dict__['_mcp_client'] = mcp_client
        self.__dict__['_is_instance'] = True
        
        # Create closure that captures client and tool info
        # This is the key pattern from DSPy - using a closure to capture state
        async def execute_mcp_tool(**kwargs):
            """Execute the MCP tool with captured client."""
            # Filter out None values - MCP server expects optional params to be omitted
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            # mcp_client and mcp_tool_info are captured from enclosing scope
            result = await mcp_client.call_tool(
                tool_name=mcp_tool_info.name,
                arguments=filtered_kwargs
            )
            return result
        
        # Store the closure as our instance function
        self.__dict__['_instance_func'] = execute_mcp_tool
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return self.__dict__.get('_instance_name', self.NAME)
    
    def _create_args_model(self, tool_info: MCPToolInfo) -> Type[BaseModel]:
        """Create a Pydantic model from MCP tool schema.
        
        Args:
            tool_info: MCP tool information with input schema
            
        Returns:
            Dynamically created Pydantic model for tool arguments
        """
        schema = tool_info.input_schema
        fields = {}
        
        if schema and "properties" in schema:
            properties = schema["properties"]
            required = schema.get("required", [])
            
            for field_name, field_schema in properties.items():
                # Map JSON schema types to Python types
                field_type = self._get_python_type(field_schema.get("type", "string"))
                
                # Check if field is required
                is_required = field_name in required
                
                # Get description
                description = field_schema.get("description", f"Parameter: {field_name}")
                
                # Create field with appropriate default
                if is_required:
                    fields[field_name] = (field_type, Field(description=description))
                else:
                    default_value = field_schema.get("default", None)
                    fields[field_name] = (field_type, Field(default=default_value, description=description))
        
        # If no schema, create a flexible model
        if not fields:
            class FlexibleArgs(BaseModel):
                """Flexible argument model for tools without schema."""
                class Config:
                    extra = "allow"
            
            return FlexibleArgs
        
        # Create dynamic model with the fields
        model_name = f"{tool_info.name.replace('-', '_').replace(' ', '_').title()}Args"
        return create_model(model_name, **fields)
    
    def _get_python_type(self, json_type: str) -> Type:
        """Convert JSON schema type to Python type.
        
        Args:
            json_type: JSON schema type string
            
        Returns:
            Corresponding Python type
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_mapping.get(json_type, Any)
    
    def execute(self, **kwargs) -> Any:
        """Execute the MCP tool using the captured closure.
        
        This is the key method that bridges our sync architecture with
        the async MCP client, following DSPy's pattern.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        instance_func = self.__dict__.get('_instance_func')
        if not instance_func:
            raise ValueError(f"No execution function for tool {self.name}")
        
        # Execute the async closure function
        result = instance_func(**kwargs)
        
        # Handle async execution in sync context (like DSPy's Tool class)
        if asyncio.iscoroutine(result):
            try:
                # Check if we're already in an async context
                loop = asyncio.get_running_loop()
                # We're in async context, can't use run_until_complete
                # This shouldn't happen in our sync-only architecture
                raise RuntimeError("MCPToolProxy.execute() called from async context")
            except RuntimeError:
                # No async context, create one (this is the normal case)
                return asyncio.run(result)
        
        return result