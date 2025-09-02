"""MCP-based Tool Set for Real Estate.

This module provides a tool set that dynamically discovers tools from an MCP server
at runtime, implementing the instance-based approach without DSPy dependency.
"""
import asyncio
import logging
from typing import List, Optional, Type
from pydantic import BaseModel, Field, PrivateAttr
import dspy

from shared.tool_utils.base_tool import BaseTool
from shared.tool_utils.base_tool_sets import ToolSet, ToolSetConfig, ToolSetTestCase
from .mcp_client import create_mcp_client, MCPClient
from .mcp_proxy import MCPToolProxy

logger = logging.getLogger(__name__)


class RealEstateMCPToolSet(ToolSet):
    """Tool set that discovers tools dynamically from MCP server.
    
    This implementation follows the instance-based pattern where tools
    are discovered at runtime and provided as instances rather than classes.
    """
    
    def __init__(self, server_url: str = "http://localhost:8000/mcp"):
        """Initialize MCP tool set with server URL.
        
        Args:
            server_url: URL of the MCP server
        """
        # Create config without tool_classes (we provide instances)
        config = ToolSetConfig(
            name="real_estate_mcp",
            description="Real Estate tools discovered dynamically from MCP server",
            tool_classes=[]  # Empty - we provide instances instead
        )
        
        super().__init__(config=config)
        
        # Store instance data directly in __dict__ to avoid Pydantic issues
        self.__dict__['_mcp_client'] = create_mcp_client(server_url)
        self.__dict__['_tool_instances'] = []
        self.__dict__['_discovered'] = False
    
    def _perform_initialization(self) -> None:
        """Perform tool discovery when the tool set is registered.
        
        This is called once by the registry during registration.
        """
        if not self.__dict__.get('_discovered', False):
            self._discover_and_create_tools()
            self.__dict__['_discovered'] = True
    
    def _discover_and_create_tools(self):
        """Discover tools from MCP server and create proxy instances."""
        try:
            mcp_client = self.__dict__.get('_mcp_client')
            if not mcp_client:
                logger.error("No MCP client available")
                return
            
            # Run async discovery in sync context
            tool_infos = asyncio.run(mcp_client.discover_tools())
            
            logger.info(f"Discovered {len(tool_infos)} tools from MCP server")
            
            # Clear any existing instances
            self.__dict__['_tool_instances'] = []
            
            # Create proxy instance for each discovered tool
            for tool_info in tool_infos:
                # Create MCPToolProxy instance for this tool
                proxy = MCPToolProxy(
                    mcp_tool_info=tool_info,
                    mcp_client=mcp_client
                )
                self.__dict__['_tool_instances'].append(proxy)
                logger.debug(f"Created proxy for tool: {tool_info.name}")
            
            logger.info(f"Created {len(self.__dict__['_tool_instances'])} tool proxies")
            
        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")
            # Continue with empty tool list on failure
    
    def provides_instances(self) -> bool:
        """Indicate that this tool set provides instances rather than classes.
        
        This is the key method that tells the registry to use our instances
        directly rather than trying to instantiate classes.
        
        Returns:
            True to indicate instance-based tool set
        """
        return True
    
    def get_tool_instances(self) -> List[BaseTool]:
        """Return the discovered tool instances.
        
        Returns:
            List of MCPToolProxy instances for discovered tools
        """
        return self.__dict__.get('_tool_instances', [])
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """Return test cases for the real estate MCP tools.
        
        Returns:
            List of test cases
        """
        return [
            ToolSetTestCase(
                tool_set="real_estate_mcp",
                scenario="property_search",
                request="Find modern homes with pools in San Francisco",
                expected_tools=["search_properties_tool"],
                description="Search for properties with specific features"
            ),
            ToolSetTestCase(
                tool_set="real_estate_mcp",
                scenario="property_details",
                request="Show me details for listing PROP-001",
                expected_tools=["get_property_details_tool"],
                description="Get detailed information about a specific property"
            ),
            ToolSetTestCase(
                tool_set="real_estate_mcp",
                scenario="location_research",
                request="Tell me about the Mission District neighborhood",
                expected_tools=["search_wikipedia_tool"],
                description="Research neighborhood information"
            ),
            ToolSetTestCase(
                tool_set="real_estate_mcp",
                scenario="location_discovery",
                request="What can you tell me about Oakland, CA?",
                expected_tools=["search_wikipedia_by_location_tool"],
                description="Discover information about a specific location"
            ),
            ToolSetTestCase(
                tool_set="real_estate_mcp",
                scenario="natural_language",
                request="I need a cozy family home near good schools",
                expected_tools=["natural_language_search_tool"],
                description="Natural language property search"
            ),
            ToolSetTestCase(
                tool_set="real_estate_mcp",
                scenario="system_check",
                request="Check if all systems are working",
                expected_tools=["health_check_tool"],
                description="System health check"
            )
        ]
    
    @classmethod
    def get_react_signature(cls) -> Optional[Type[dspy.Signature]]:
        """Return custom React signature for real estate domain.
        
        Returns:
            Custom signature with real estate-specific instructions
        """
        class RealEstateReactSignature(dspy.Signature):
            """React signature for real estate tool execution."""
            
            # Inputs
            trajectory: str = dspy.InputField(
                desc="Previous thoughts, actions, and observations"
            )
            context_prompt: str = dspy.InputField(
                desc="User context and conversation history"
            )
            tools: str = dspy.InputField(
                desc="Available real estate tools and their descriptions"
            )
            user_request: str = dspy.InputField(
                desc="The user's current request"
            )
            
            # Outputs  
            thought: str = dspy.OutputField(
                desc="Current reasoning about what to do next"
            )
            tool_name: str = dspy.OutputField(
                desc="Name of the tool to use (must be from available tools)"
            )
            tool_args: dict = dspy.OutputField(
                desc="Arguments for the selected tool as a dictionary"
            )
        
        return RealEstateReactSignature
    
    @classmethod
    def get_extract_signature(cls) -> Optional[Type[dspy.Signature]]:
        """Return custom Extract signature for real estate domain.
        
        Returns:
            Custom signature for final answer synthesis
        """
        class RealEstateExtractSignature(dspy.Signature):
            """Extract signature for synthesizing real estate information."""
            
            # Inputs
            trajectory: str = dspy.InputField(
                desc="Complete trajectory of thoughts, actions, and observations"
            )
            user_request: str = dspy.InputField(
                desc="The original user request"
            )
            
            # Outputs
            final_answer: str = dspy.OutputField(
                desc="Comprehensive answer about properties, neighborhoods, or real estate information"
            )
        
        return RealEstateExtractSignature