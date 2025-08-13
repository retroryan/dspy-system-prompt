"""Search products tool implementation using the unified base class."""
import json
from pathlib import Path
from typing import List, Optional, ClassVar, Dict, Any, Type, Union
from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class SearchProductsTool(BaseTool):
    """Tool for searching products in the catalog."""
    
    NAME: ClassVar[str] = "search_products"
    MODULE: ClassVar[str] = "tools.ecommerce.search_products"
    
    class Arguments(BaseModel):
        """Arguments for searching products."""
        query: str = Field(..., description="Search query")
        category: Optional[str] = Field(default=None, description="Product category")
        max_price: Optional[float] = Field(default=None, ge=0, description="Maximum price")
        
        @field_validator('max_price', mode='before')
        @classmethod
        def validate_max_price(cls, v) -> Optional[float]:
            """Convert string to float for max_price."""
            if v is None or v == "" or str(v).lower() in ["null", "none"]:
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None
    
    # Tool definition as instance attributes
    description: str = "Search for products in the catalog"
    args_model: Type[BaseModel] = Arguments
    
    def execute(self, query: str, category: str = None, max_price: Union[float, str, None] = None) -> dict:
        """Execute the tool to search products."""
        # Load products from JSON file
        file_path = Path(__file__).resolve().parent.parent / "data" / "products.json"
        
        if not file_path.exists():
            return {"error": "Products data file not found."}
        
        with open(file_path, "r") as file:
            data = json.load(file)
        
        all_products = data["products"]
        
        # Filter products based on query
        matching_products = []
        query_lower = query.lower()
        
        for product in all_products:
            # Check if query matches name, category, or subcategory
            if (query_lower in product["name"].lower() or
                (product.get("category") and query_lower in product["category"].lower()) or
                (product.get("subcategory") and query_lower in product["subcategory"].lower())):
                matching_products.append({
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "rating": product["rating"],
                    "stock": product.get("stock", 0)
                })
        
        # Apply category filter if specified
        if category:
            category_lower = category.lower()
            matching_products = [
                p for p in matching_products
                if any(product["id"] == p["id"] and 
                      (product.get("category", "").lower() == category_lower or 
                       product.get("subcategory", "").lower() == category_lower)
                      for product in all_products)
            ]
        
        # Apply price filter
        if max_price is not None:
            try:
                max_price_float = float(max_price)
                matching_products = [p for p in matching_products if p["price"] <= max_price_float]
            except (ValueError, TypeError):
                pass  # Skip price filtering if conversion fails
        
        return {
            "products": matching_products,
            "count": len(matching_products),
            "query": query,
            "best_match": matching_products[0] if matching_products else None,
            "filters": {
                "category": category,
                "max_price": max_price
            }
        }
    
    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Search for laptops under $1000",
                expected_tools=["search_products"],
                description="Search with price filter"
            ),
            ToolTestCase(
                request="Find electronics in the catalog",
                expected_tools=["search_products"],
                description="Search by category"
            ),
            ToolTestCase(
                request="Look for wireless headphones",
                expected_tools=["search_products"],
                description="General product search"
            )
        ]