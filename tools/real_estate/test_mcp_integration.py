"""Test script for MCP tool integration.

This script tests the complete MCP integration including:
1. Connecting to the MCP server
2. Discovering tools dynamically
3. Creating tool proxies
4. Registering with the tool registry
5. Executing tools through the registry
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.tool_utils.registry import ToolRegistry
from tools.real_estate.mcp_tool_set import RealEstateMCPToolSet
from tools.real_estate.mcp_client import create_mcp_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_mcp_client_connection():
    """Test basic MCP client connection and tool discovery."""
    print("\n" + "="*60)
    print("Test 1: MCP Client Connection and Discovery")
    print("="*60)
    
    client = create_mcp_client("http://localhost:8000/mcp")
    
    # Test discovery
    tools = asyncio.run(client.discover_tools())
    
    print(f"✓ Connected to MCP server")
    print(f"✓ Discovered {len(tools)} tools:")
    
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")
    
    return len(tools) > 0


def test_mcp_tool_set_creation():
    """Test creating MCP tool set and discovering tools."""
    print("\n" + "="*60)
    print("Test 2: MCP Tool Set Creation")
    print("="*60)
    
    # Create tool set
    tool_set = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    
    print(f"✓ Created RealEstateMCPToolSet")
    print(f"  - Name: {tool_set.config.name}")
    print(f"  - Description: {tool_set.config.description}")
    print(f"  - Provides instances: {tool_set.provides_instances()}")
    
    # Initialize (discover tools)
    tool_set.initialize()
    
    # Get instances
    instances = tool_set.get_tool_instances()
    print(f"✓ Discovered and created {len(instances)} tool proxies:")
    
    for instance in instances:
        print(f"  - {instance.name}: {instance.description[:50]}...")
    
    return len(instances) > 0


def test_registry_integration():
    """Test registering MCP tool set with the registry."""
    print("\n" + "="*60)
    print("Test 3: Registry Integration")
    print("="*60)
    
    # Create registry and tool set
    registry = ToolRegistry()
    tool_set = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    
    # Register tool set
    registry.register_tool_set(tool_set)
    
    print(f"✓ Registered tool set with registry")
    
    # Check registered tools
    tool_names = registry.get_tool_names()
    print(f"✓ Registry contains {len(tool_names)} tools:")
    
    for name in tool_names:
        tool = registry.get_tool(name)
        if tool:
            print(f"  - {name}: {tool.description[:50]}...")
    
    return len(tool_names) > 0


def test_tool_execution():
    """Test executing an MCP tool through the registry."""
    print("\n" + "="*60)
    print("Test 4: Tool Execution")
    print("="*60)
    
    # Create and register tool set
    registry = ToolRegistry()
    tool_set = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    registry.register_tool_set(tool_set)
    
    # Test search_properties_tool
    tool_name = "search_properties_tool"
    
    if tool_name not in registry.get_tool_names():
        print(f"✗ Tool '{tool_name}' not found in registry")
        print(f"  Available tools: {registry.get_tool_names()}")
        return False
    
    print(f"✓ Found '{tool_name}' in registry")
    
    # Create tool call
    from shared.models import ToolCall
    tool_call = ToolCall(
        tool_name=tool_name,
        arguments={
            "query": "modern home with pool",
            "size": 3
        }
    )
    
    print(f"✓ Executing tool with query: 'modern home with pool'")
    
    # Execute tool
    result = registry.execute_tool(tool_call)
    
    if result.success:
        print(f"✓ Tool execution successful!")
        print(f"  - Execution time: {result.execution_time:.3f}s")
        
        # Display result preview
        if result.result:
            import json
            result_str = json.dumps(result.result, indent=2)
            if len(result_str) > 500:
                result_str = result_str[:500] + "..."
            print(f"  - Result preview:\n{result_str}")
    else:
        print(f"✗ Tool execution failed: {result.error}")
    
    return result.success


def test_health_check():
    """Test the health check tool."""
    print("\n" + "="*60)
    print("Test 5: Health Check Tool")
    print("="*60)
    
    # Create and register tool set
    registry = ToolRegistry()
    tool_set = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    registry.register_tool_set(tool_set)
    
    # Test health_check_tool
    tool_name = "health_check_tool"
    
    if tool_name not in registry.get_tool_names():
        print(f"✗ Tool '{tool_name}' not found in registry")
        return False
    
    print(f"✓ Found '{tool_name}' in registry")
    
    # Create tool call
    from shared.models import ToolCall
    tool_call = ToolCall(
        tool_name=tool_name,
        arguments={}  # No arguments needed
    )
    
    print(f"✓ Executing health check...")
    
    # Execute tool
    result = registry.execute_tool(tool_call)
    
    if result.success:
        print(f"✓ Health check successful!")
        print(f"  - Execution time: {result.execution_time:.3f}s")
        
        # Display health status
        if result.result:
            import json
            print(f"  - System status:\n{json.dumps(result.result, indent=4)}")
    else:
        print(f"✗ Health check failed: {result.error}")
    
    return result.success


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MCP Tool Integration Test Suite")
    print("="*60)
    print(f"Server URL: http://localhost:8000/mcp")
    
    # Track results
    results = []
    
    # Run tests
    try:
        results.append(("Client Connection", test_mcp_client_connection()))
    except Exception as e:
        logger.error(f"Client connection test failed: {e}")
        results.append(("Client Connection", False))
    
    try:
        results.append(("Tool Set Creation", test_mcp_tool_set_creation()))
    except Exception as e:
        logger.error(f"Tool set creation test failed: {e}")
        results.append(("Tool Set Creation", False))
    
    try:
        results.append(("Registry Integration", test_registry_integration()))
    except Exception as e:
        logger.error(f"Registry integration test failed: {e}")
        results.append(("Registry Integration", False))
    
    try:
        results.append(("Tool Execution", test_tool_execution()))
    except Exception as e:
        logger.error(f"Tool execution test failed: {e}")
        results.append(("Tool Execution", False))
    
    try:
        results.append(("Health Check", test_health_check()))
    except Exception as e:
        logger.error(f"Health check test failed: {e}")
        results.append(("Health Check", False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! MCP integration is working correctly.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please check the logs above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)