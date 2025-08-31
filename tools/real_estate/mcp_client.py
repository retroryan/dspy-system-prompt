"""MCP Client for Real Estate Tools.

This module provides a simple client for connecting to the MCP server
and discovering tools dynamically. Based on the real implementation from
real_estate_ai_search project.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Import FastMCP client
from fastmcp import Client

logger = logging.getLogger(__name__)


class MCPToolInfo(BaseModel):
    """Information about a discovered MCP tool."""
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="Tool input schema")


class MCPClient(BaseModel):
    """Simple MCP client that connects to the real estate MCP server."""
    
    server_url: str = Field(default="http://localhost:8000/mcp", description="MCP server URL")
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    
    async def discover_tools(self) -> List[MCPToolInfo]:
        """Discover available tools from MCP server.
        
        Returns:
            List of discovered tool information
        """
        tools_list = []
        
        try:
            # FastMCP Client automatically detects HTTP transport from URL
            async with Client(self.server_url) as client:
                if not client.is_connected():
                    logger.error("Failed to connect to MCP server")
                    return []
                
                # List available tools
                tools = await client.list_tools()
                
                # Convert to our tool info format
                for tool in tools:
                    # Extract tool information
                    tool_info = MCPToolInfo(
                        name=tool.name,
                        description=tool.description or f"Tool: {tool.name}",
                        input_schema={}
                    )
                    
                    # Parse input schema if available
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        schema = tool.inputSchema
                        if isinstance(schema, dict):
                            tool_info.input_schema = schema
                        elif hasattr(schema, 'model_dump'):
                            tool_info.input_schema = schema.model_dump()
                        else:
                            tool_info.input_schema = {"raw": str(schema)}
                    
                    tools_list.append(tool_info)
                    
                logger.info(f"Discovered {len(tools_list)} tools from MCP server")
                
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
        
        return tools_list
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            async with Client(self.server_url) as client:
                if not client.is_connected():
                    raise Exception("Failed to connect to MCP server")
                
                # Call the tool
                result = await client.call_tool(tool_name, arguments=arguments)
                
                # Parse result based on type
                if hasattr(result, 'content'):
                    # Handle MCP response format
                    content = result.content
                    if isinstance(content, list) and len(content) > 0:
                        # Extract text content from first item
                        first_item = content[0]
                        if hasattr(first_item, 'text'):
                            return first_item.text
                        elif hasattr(first_item, 'data'):
                            return first_item.data
                        else:
                            return str(first_item)
                    return content
                else:
                    # Direct result
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {e}")
            raise


def create_mcp_client(server_url: str = "http://localhost:8000/mcp") -> MCPClient:
    """Create an MCP client instance.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        MCPClient instance
    """
    return MCPClient(server_url=server_url)