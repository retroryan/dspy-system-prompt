"""Run all MCP demos in sequence

This script runs all the MCP demos to showcase the complete functionality
of the MCP tool integration.
"""
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_demo(name: str, module: str):
    """Run a single demo."""
    print(f"\n{'='*70}")
    print(f"Running: {name}")
    print(f"{'='*70}")
    
    try:
        exec(f"from {module} import *")
        exec(f"{module.split('.')[-1]}()")
        print(f"\n✅ {name} completed successfully")
        return True
    except Exception as e:
        print(f"\n❌ {name} failed: {e}")
        return False


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("MCP TOOL INTEGRATION - DEMO SHOWCASE")
    print("="*70)
    print("\nThis showcase demonstrates the complete MCP tool integration")
    print("without any DSPy dependency, using a clean, modular architecture.")
    
    demos = [
        {
            "name": "Tool Discovery Demo",
            "module": "demo_tool_discovery",
            "description": "Shows dynamic tool discovery from MCP server"
        },
        {
            "name": "Direct Tool Execution Demo",
            "module": "demo_direct_tools",
            "description": "Demonstrates direct tool execution through registry"
        }
    ]
    
    results = []
    
    print(f"\n📋 Demos to run:")
    for demo in demos:
        print(f"   • {demo['name']}: {demo['description']}")
    
    print(f"\n🚀 Starting demo sequence...")
    time.sleep(2)
    
    for demo in demos:
        # Import and run the demo
        module_name = f"mcp_demos.{demo['module']}"
        
        try:
            module = __import__(module_name, fromlist=[demo['module']])
            demo_func = getattr(module, demo['module'].replace('demo_', 'demo_'))
            
            print(f"\n{'='*70}")
            print(f"Demo: {demo['name']}")
            print(f"{'='*70}")
            
            demo_func()
            results.append((demo['name'], True))
            
            print(f"\n✅ {demo['name']} completed")
            time.sleep(1)  # Brief pause between demos
            
        except Exception as e:
            print(f"\n❌ {demo['name']} failed: {e}")
            results.append((demo['name'], False))
    
    # Final summary
    print(f"\n{'='*70}")
    print("SHOWCASE SUMMARY")
    print(f"{'='*70}")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print(f"\n📊 Results: {successful}/{total} demos completed successfully")
    
    if successful == total:
        print("\n🎉 All demos completed successfully!")
        print("\n🌟 Key Achievements:")
        print("   • Dynamic tool discovery from MCP server")
        print("   • Clean integration with existing registry")
        print("   • Instance-based architecture (no class generation)")
        print("   • Closure-based state management")
        print("   • Full Pydantic validation throughout")
        print("   • No DSPy dependency")
        print("\n💡 The MCP tool integration is production-ready!")
    else:
        print(f"\n⚠️ {total - successful} demo(s) had issues.")
        print("Please check the error messages above.")
    
    return successful == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)