"""Demo: Dynamic Tool Discovery and Introspection

This demo showcases the dynamic discovery capabilities of MCP tools,
showing how tools are discovered at runtime from the server.
"""
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.real_estate.mcp_client import create_mcp_client
from tools.real_estate.mcp_tool_set import RealEstateMCPToolSet
from shared.tool_utils.registry import ToolRegistry
from shared.models import ToolCall


def display_tool_schema(tool_name: str, tool_instance):
    """Display detailed information about a tool."""
    print(f"\n📦 Tool: {tool_name}")
    print(f"   Description: {tool_instance.description}")
    
    # Show arguments
    if tool_instance.arguments:
        print("   Arguments:")
        for arg in tool_instance.arguments:
            required = "required" if arg.required else "optional"
            default = f" (default: {arg.default})" if arg.default is not None else ""
            print(f"      - {arg.name} ({arg.type}): {required}{default}")
            if arg.description:
                print(f"        {arg.description[:80]}")
    else:
        print("   No arguments required")


async def discover_tools_async():
    """Discover tools from MCP server asynchronously."""
    client = create_mcp_client("http://localhost:8000/mcp")
    tools = await client.discover_tools()
    if not tools:
        raise Exception("No tools discovered from MCP server. Please ensure the server is running.")
    return tools


def demo_tool_discovery():
    """Demonstrate dynamic tool discovery from MCP server."""
    
    print("\n" + "="*70)
    print("DEMO: Dynamic MCP Tool Discovery")
    print("="*70)
    print("Discovering tools at runtime from MCP server")
    
    # Step 1: Direct discovery from MCP server
    print("\n🔍 Step 1: Direct Discovery from MCP Server")
    print("-" * 40)
    
    print("Connecting to MCP server at http://localhost:8000/mcp...")
    
    # Discover tools directly
    discovered_tools = asyncio.run(discover_tools_async())
    
    print(f"\n✅ Discovered {len(discovered_tools)} tools from MCP server:")
    for i, tool_info in enumerate(discovered_tools, 1):
        print(f"\n   {i}. {tool_info.name}")
        print(f"      {tool_info.description[:100]}...")
        
        # Show schema info
        if tool_info.input_schema and "properties" in tool_info.input_schema:
            props = tool_info.input_schema["properties"]
            required = tool_info.input_schema.get("required", [])
            print(f"      Parameters: {len(props)} total, {len(required)} required")
    
    # Step 2: Tool Set Integration
    print(f"\n🔧 Step 2: Integration with Tool Set")
    print("-" * 40)
    
    print("Creating MCP tool set...")
    tool_set = RealEstateMCPToolSet(server_url="http://localhost:8000/mcp")
    
    # Initialize to discover tools
    tool_set.initialize()
    
    # Get tool instances
    instances = tool_set.get_tool_instances()
    print(f"\n✅ Tool set created {len(instances)} proxy instances")
    print(f"   Tool set name: {tool_set.config.name}")
    print(f"   Description: {tool_set.config.description}")
    print(f"   Provides instances: {tool_set.provides_instances()}")
    
    # Step 3: Registry Integration
    print(f"\n📚 Step 3: Registry Integration")
    print("-" * 40)
    
    print("Registering tool set with registry...")
    registry = ToolRegistry()
    registry.register_tool_set(tool_set)
    
    registered_tools = registry.get_tool_names()
    print(f"\n✅ Registry now contains {len(registered_tools)} tools")
    
    # Show detailed info for each tool
    print("\n📋 Detailed Tool Information:")
    print("-" * 40)
    
    # Group tools by category
    search_tools = []
    info_tools = []
    system_tools = []
    
    for tool_name in registered_tools:
        if "search" in tool_name or "natural" in tool_name:
            search_tools.append(tool_name)
        elif "details" in tool_name or "wikipedia" in tool_name:
            info_tools.append(tool_name)
        else:
            system_tools.append(tool_name)
    
    # Display by category
    if search_tools:
        print("\n🔍 Search Tools:")
        for tool_name in search_tools:
            tool = registry.get_tool(tool_name)
            display_tool_schema(tool_name, tool)
    
    if info_tools:
        print("\n📖 Information Tools:")
        for tool_name in info_tools:
            tool = registry.get_tool(tool_name)
            display_tool_schema(tool_name, tool)
    
    if system_tools:
        print("\n⚙️ System Tools:")
        for tool_name in system_tools:
            tool = registry.get_tool(tool_name)
            display_tool_schema(tool_name, tool)
    
    # Step 5: Live Tool Execution Example
    print(f"\n🚀 Step 5: Live Tool Execution Example")
    print("-" * 40)
    
    print("\nExecuting health check to verify server connectivity...")
    
    # Try health check
    health_call = ToolCall(
        tool_name="health_check_tool",
        arguments={}
    )
    
    result = registry.execute_tool(health_call)
    if result.success:
        print("\n✅ Health Check Results:")
        if isinstance(result.result, str):
            try:
                data = json.loads(result.result)
                print(f"   Status: {data.get('status', 'unknown').upper()}")
                print(f"   Timestamp: {datetime.now().isoformat()}")
                services = data.get('services', {})
                for service, info in services.items():
                    status = info.get('status', 'unknown')
                    emoji = "✅" if status == "healthy" else "⚠️"
                    print(f"   {emoji} {service}: {info.get('message', 'No message')}")
            except:
                print(f"   Result: {result.result}")
        else:
            print(f"   Result: {result.result}")
        print(f"   Execution time: {result.execution_time:.3f}s")
    else:
        print(f"❌ Health check failed: {result.error}")
        raise Exception(f"Server health check failed: {result.error}")
    
    # Step 6: Demonstrate Dynamic Nature
    print(f"\n🎯 Step 6: Dynamic Nature Demonstration")
    print("-" * 40)
    
    print("\n💡 Key Points:")
    print("   • Tools were NOT defined in code - discovered from server")
    print("   • Tool schemas automatically converted to Pydantic models")
    print("   • Each tool is a proxy instance with captured MCP client")
    print("   • Tools integrate seamlessly with existing registry")
    print("   • No DSPy dependency - clean, modular implementation")
    print("   • Server provides real-time tool availability")
    print("   • Tools can be added/removed on server without code changes")
    
    # Summary
    print(f"\n{'='*70}")
    print("DISCOVERY SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Successfully discovered {len(discovered_tools)} tools from MCP server")
    print(f"🔧 Created proxy instances for all discovered tools")
    print(f"📚 Integrated with registry for standard access pattern")
    print(f"🚀 Tools ready for use in agent sessions or direct execution")
    
    print("\n🌟 This demonstrates the power of dynamic tool discovery:")
    print("   - Zero hardcoding of tool definitions")
    print("   - Server can add/remove tools without code changes")
    print("   - Clean separation between tool discovery and usage")
    print("   - Instance-based architecture avoids class generation complexity")


if __name__ == "__main__":
    try:
        demo_tool_discovery()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Make sure the MCP server is running at http://localhost:8000/mcp")
        sys.exit(1)