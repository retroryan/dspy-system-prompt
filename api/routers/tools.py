"""
Tool set information endpoints.

Provides information about available tool sets and their capabilities.
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from api.core.models import ToolSetInfo
from api.middleware.error_handler import ToolSetNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tool-sets", tags=["Tools"])


def get_tool_set_info(name: str) -> ToolSetInfo:
    """
    Get information about a specific tool set.
    
    Args:
        name: Tool set name
        
    Returns:
        Tool set information
        
    Raises:
        ToolSetNotFoundException: If tool set doesn't exist
    """
    tool_sets = {
        "agriculture": ToolSetInfo(
            name="agriculture",
            description="Precision agriculture tools for weather, soil, and crop management",
            tools=[
                "GetWeather",
                "GetSoilConditions",
                "GetCropRecommendations",
                "AnalyzeField",
                "GetIrrigationSchedule"
            ],
            example_queries=[
                "What's the weather forecast for my farm?",
                "Check soil conditions for field A",
                "What crops should I plant this season?",
                "Analyze the northeast field conditions",
                "When should I irrigate my wheat field?"
            ]
        ),
        "ecommerce": ToolSetInfo(
            name="ecommerce",
            description="E-commerce tools for orders, products, cart, and customer management",
            tools=[
                "GetOrders",
                "GetOrderDetails",
                "GetProducts",
                "SearchProducts",
                "GetCart",
                "AddToCart",
                "RemoveFromCart",
                "Checkout",
                "ProcessReturn",
                "GetCustomerInfo"
            ],
            example_queries=[
                "Show me my recent orders",
                "Find laptops under $1000",
                "Add item to my cart",
                "Process checkout with my saved address",
                "Return item from order #12345",
                "What's in my shopping cart?"
            ]
        ),
        "events": ToolSetInfo(
            name="events",
            description="Event management tools for scheduling, venues, and registrations",
            tools=[
                "GetEvents",
                "SearchEvents",
                "GetVenues",
                "CheckAvailability",
                "CreateBooking",
                "GetRegistrations",
                "RegisterForEvent",
                "CancelRegistration",
                "GetEventDetails",
                "UpdateEvent"
            ],
            example_queries=[
                "What events are happening this weekend?",
                "Find tech conferences in San Francisco",
                "Check venue availability for June 15",
                "Register me for the AI summit",
                "Cancel my registration for event #789",
                "Show me all my event registrations"
            ]
        ),
        "real_estate_mcp": ToolSetInfo(
            name="real_estate_mcp",
            description="Real Estate tools powered by MCP for property search and neighborhood information",
            tools=[
                "search_properties_tool",
                "get_property_details_tool",
                "search_wikipedia_tool",
                "find_property_images_tool",
                "analyze_images_tool",
                "scrape_url_tool"
            ],
            example_queries=[
                "Find modern family homes with pools in Oakland under $800k",
                "Tell me about the Temescal neighborhood in Oakland",
                "Search luxury properties with stunning views",
                "Show me family homes near top-rated schools in San Francisco",
                "Get details for property ID 123456",
                "Find condos with ocean views in Berkeley"
            ]
        )
    }
    
    if name not in tool_sets:
        raise ToolSetNotFoundException(name)
    
    return tool_sets[name]


@router.get("", response_model=List[ToolSetInfo])
def list_tool_sets():
    """
    List all available tool sets.
    
    Returns information about all tool sets including their
    available tools and example queries.
    
    Returns:
        List of tool set information
    """
    tool_sets = []
    for name in ["agriculture", "ecommerce", "events", "real_estate_mcp"]:
        try:
            tool_sets.append(get_tool_set_info(name))
        except Exception as e:
            logger.error(f"Failed to get info for tool set {name}: {str(e)}")
    
    return tool_sets


@router.get("/{name}", response_model=ToolSetInfo)
def get_tool_set(name: str):
    """
    Get detailed information about a specific tool set.
    
    Returns information about the tool set including available
    tools and example queries.
    
    Args:
        name: Tool set name (agriculture, ecommerce, events)
        
    Returns:
        Tool set information
        
    Raises:
        404: Tool set not found
    """
    try:
        return get_tool_set_info(name)
    except ToolSetNotFoundException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get tool set {name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool set information: {str(e)}"
        )