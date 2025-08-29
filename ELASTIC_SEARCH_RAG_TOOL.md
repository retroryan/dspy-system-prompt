# Elasticsearch Real Estate RAG Tool Implementation

## Executive Summary

This proposal outlines the integration of the existing Elasticsearch-based real estate search system with the DSPy agentic framework. The system leverages an already operational API with 2,262+ vector embeddings, Wikipedia enrichment, and sophisticated search capabilities. The tool will provide RAG-enhanced property search while maintaining the DSPy principle of simplicity and type safety.

## Current System Analysis

### Existing Infrastructure

The real estate search system currently provides:

- **Elasticsearch Index**: Fully indexed properties with Wikipedia enrichment
- **Vector Storage**: ChromaDB with 2,262+ embeddings using nomic-embed-text (768 dimensions)
- **FastAPI Server**: Production-ready API with comprehensive endpoints
- **Wikipedia Integration**: SQLite database with location context and POI data
- **Hybrid Search**: BM25 relevance + vector similarity + Wikipedia enrichment scores

### Available API Endpoints

```
POST /api/search          - Multi-field text search with Wikipedia enhancement
POST /api/geo-search      - Geographic radius search
GET  /api/properties/{id} - Individual property details  
POST /api/properties/{id}/similar - Content-based similarity
GET  /api/stats          - Market statistics and aggregations
```

## Implementation Strategy

### Phase 1: API Client Integration

Create a lightweight client that interfaces with the existing FastAPI server. The client will accept structured parameters from the React agent, avoiding any NLP processing on the API server side:

```python
# tools/real_estate_rag/api_client.py
import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ElasticsearchClient:
    """Client for existing real estate search API - accepts structured parameters only"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
    
    def search(
        self,
        keywords: Optional[List[str]] = None,
        features: Optional[List[str]] = None,
        amenities: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        enable_wikipedia: bool = True
    ) -> SearchResponse:
        """Execute search with structured parameters - no NLP needed"""
        
        # Build Elasticsearch query from structured inputs
        query_parts = []
        
        if keywords:
            query_parts.append(" ".join(keywords))
        
        if features:
            # Features go into specific feature field matching
            if not filters:
                filters = {}
            filters["features"] = features
        
        if amenities:
            if not filters:
                filters = {}
            filters["amenities"] = amenities
        
        payload = {
            "query": " ".join(query_parts) if query_parts else "",
            "filters": filters or {},
            "limit": limit,
            "include_wikipedia": enable_wikipedia,
            "boost_wikipedia": 2.0 if enable_wikipedia else 0
        }
        
        response = self.client.post(
            f"{self.base_url}/api/search",
            json=payload
        )
        response.raise_for_status()
        return SearchResponse(**response.json())
    
    def geo_search(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """Geographic radius search with explicit coordinates"""
        
        payload = {
            "location": {"lat": latitude, "lon": longitude},
            "radius": f"{radius_miles}mi",
            "filters": filters or {}
        }
        
        response = self.client.post(
            f"{self.base_url}/api/geo-search",
            json=payload
        )
        response.raise_for_status()
        return SearchResponse(**response.json())
```

### Phase 2: Tool Implementation

```python
# tools/real_estate_rag/property_search.py
from typing import ClassVar, Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from shared.tool_utils.base_tool import BaseTool
from shared.tool_utils.error_handling import safe_tool_execution

class PropertySearchTool(BaseTool):
    """RAG-enhanced real estate search using Elasticsearch + Wikipedia"""
    
    NAME: ClassVar[str] = "search_properties"
    MODULE: ClassVar[str] = "tools.real_estate_rag.property_search"
    
    class Arguments(BaseModel):
        """Structured arguments for property search - no NLP processing needed"""
        # Structured search terms instead of natural language
        keywords: Optional[List[str]] = Field(None, description="Search keywords e.g., ['modern', 'spacious', 'renovated']")
        features: Optional[List[str]] = Field(None, description="Required features e.g., ['pool', 'garage', 'fireplace']")
        amenities: Optional[List[str]] = Field(None, description="Desired amenities e.g., ['gym', 'parking', 'balcony']")
        
        # Location filters
        state: Optional[str] = Field(None, description="State filter (CA or UT only)")
        city: Optional[str] = Field(None, description="City name filter")
        neighborhood: Optional[str] = Field(None, description="Neighborhood name")
        
        # Numeric filters
        price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
        price_max: Optional[float] = Field(None, ge=0, description="Maximum price")
        bedrooms_min: Optional[int] = Field(None, ge=0, description="Minimum bedrooms")
        bedrooms_max: Optional[int] = Field(None, ge=0, description="Maximum bedrooms")
        bathrooms_min: Optional[float] = Field(None, ge=0, description="Minimum bathrooms")
        square_feet_min: Optional[int] = Field(None, ge=0, description="Minimum square feet")
        square_feet_max: Optional[int] = Field(None, ge=0, description="Maximum square feet")
        year_built_min: Optional[int] = Field(None, ge=1800, description="Minimum year built")
        
        # Property characteristics
        property_type: Optional[str] = Field(None, description="Property type: single_family, condo, townhouse, multi_family")
        
        # Search options
        enable_wikipedia: bool = Field(True, description="Include Wikipedia enrichment")
        sort_by: Optional[str] = Field("relevance", description="Sort by: relevance, price_asc, price_desc, newest, size")
        limit: int = Field(5, ge=1, le=20, description="Number of results")
    
    description: str = "Search for real estate properties in California and Utah with structured parameters"
    args_model: Type[BaseModel] = Arguments
    
    def __init__(self):
        super().__init__()
        self.client = ElasticsearchClient()
        self.valid_states = {"CA", "CALIFORNIA", "UT", "UTAH"}
    
    @safe_tool_execution
    def execute(
        self,
        keywords: Optional[List[str]] = None,
        features: Optional[List[str]] = None,
        amenities: Optional[List[str]] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        neighborhood: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        bedrooms_min: Optional[int] = None,
        bedrooms_max: Optional[int] = None,
        bathrooms_min: Optional[float] = None,
        square_feet_min: Optional[int] = None,
        square_feet_max: Optional[int] = None,
        year_built_min: Optional[int] = None,
        property_type: Optional[str] = None,
        enable_wikipedia: bool = True,
        sort_by: Optional[str] = "relevance",
        limit: int = 5
    ) -> dict:
        """Execute property search with structured parameters"""
        
        # Validate state if provided
        if state and state.upper() not in self.valid_states:
            return {
                "error": "Invalid state",
                "message": "This tool only searches properties in California (CA) and Utah (UT)",
                "suggestion": "Please specify CA or UT, or search by city name like San Francisco or Salt Lake City"
            }
        
        # Auto-detect state from city if not provided
        if not state and city:
            city_upper = city.upper()
            ca_cities = ["SAN FRANCISCO", "LOS ANGELES", "SAN DIEGO", "SAN JOSE", "OAKLAND", "SACRAMENTO", "PALO ALTO"]
            ut_cities = ["SALT LAKE CITY", "PARK CITY", "PROVO", "OGDEN", "ST GEORGE", "LOGAN"]
            
            if any(ca_city in city_upper for ca_city in ca_cities):
                state = "CA"
            elif any(ut_city in city_upper for ut_city in ut_cities):
                state = "UT"
        
        # Build filters for the API
        filters = {}
        
        if state:
            filters["state"] = state.upper()
        
        if city:
            filters["city"] = city
            
        if neighborhood:
            filters["neighborhood"] = neighborhood
            
        if price_min or price_max:
            filters["price_range"] = {}
            if price_min:
                filters["price_range"]["gte"] = price_min
            if price_max:
                filters["price_range"]["lte"] = price_max
        
        if bedrooms_min or bedrooms_max:
            filters["bedrooms_range"] = {}
            if bedrooms_min:
                filters["bedrooms_range"]["gte"] = bedrooms_min
            if bedrooms_max:
                filters["bedrooms_range"]["lte"] = bedrooms_max
            
        if bathrooms_min:
            filters["bathrooms_min"] = bathrooms_min
            
        if square_feet_min or square_feet_max:
            filters["sqft_range"] = {}
            if square_feet_min:
                filters["sqft_range"]["gte"] = square_feet_min
            if square_feet_max:
                filters["sqft_range"]["lte"] = square_feet_max
                
        if year_built_min:
            filters["year_built_min"] = year_built_min
            
        if property_type:
            filters["property_type"] = property_type
        
        # Execute search with structured parameters
        try:
            response = self.client.search(
                keywords=keywords,
                features=features,
                amenities=amenities,
                filters=filters,
                limit=limit,
                enable_wikipedia=enable_wikipedia
            )
            
            # Format results with Wikipedia insights
            results = []
            for prop in response.properties:
                result = {
                    "listing_id": prop.listing_id,
                    "address": f"{prop.address.street}, {prop.address.city}, {prop.address.state}",
                    "price": prop.price,
                    "details": {
                        "bedrooms": prop.bedrooms,
                        "bathrooms": prop.bathrooms,
                        "square_feet": prop.square_feet,
                        "year_built": prop.year_built,
                        "property_type": prop.property_type
                    },
                    "features": prop.features[:5] if prop.features else [],
                    "amenities": prop.amenities[:5] if prop.amenities else [],
                    "description": prop.description[:200] + "..." if prop.description else "",
                    "score": prop.search_score
                }
                
                # Add Wikipedia enrichment if available
                if prop.wikipedia_context:
                    result["neighborhood_insights"] = {
                        "summary": prop.wikipedia_context.summary[:200] + "...",
                        "cultural_score": prop.wikipedia_context.cultural_richness_score,
                        "historical_importance": prop.wikipedia_context.historical_importance_score,
                        "nearby_landmarks": [
                            f"{poi.name} ({poi.distance_miles:.1f} mi)"
                            for poi in prop.wikipedia_context.nearby_pois[:3]
                        ],
                        "key_topics": prop.wikipedia_context.key_topics[:5]
                    }
                
                results.append(result)
            
            # Sort results if requested
            if sort_by == "price_asc":
                results.sort(key=lambda x: x["price"])
            elif sort_by == "price_desc":
                results.sort(key=lambda x: x["price"], reverse=True)
            elif sort_by == "size":
                results.sort(key=lambda x: x["details"]["square_feet"] or 0, reverse=True)
            elif sort_by == "newest":
                results.sort(key=lambda x: x["details"]["year_built"] or 0, reverse=True)
            
            return {
                "found": len(results),
                "search_criteria": {
                    "keywords": keywords,
                    "features": features,
                    "amenities": amenities,
                    "location": {
                        "state": state,
                        "city": city,
                        "neighborhood": neighborhood
                    } if any([state, city, neighborhood]) else None,
                    "filters": filters
                },
                "properties": results,
                "search_metadata": {
                    "wikipedia_enhanced": enable_wikipedia,
                    "total_available": response.total,
                    "search_time_ms": response.search_time_ms,
                    "sort_by": sort_by
                }
            }
            
        except Exception as e:
            return {
                "error": "Search failed",
                "message": str(e),
                "suggestion": "Try adjusting your search criteria"
            }
```

### Phase 3: Geographic Search Tool

```python
# tools/real_estate_rag/geo_search.py
class GeoSearchTool(BaseTool):
    """Geographic radius search for properties"""
    
    NAME: ClassVar[str] = "geo_search_properties"
    MODULE: ClassVar[str] = "tools.real_estate_rag.geo_search"
    
    class Arguments(BaseModel):
        location: str = Field(..., description="Location name or address")
        radius_miles: float = Field(10, ge=1, le=50, description="Search radius in miles")
        price_max: Optional[float] = Field(None, description="Maximum price filter")
        property_type: Optional[str] = Field(None, description="Property type filter")
    
    description: str = "Search properties within a geographic radius"
    args_model: Type[BaseModel] = Arguments
    
    @safe_tool_execution
    def execute(
        self,
        location: str,
        radius_miles: float = 10,
        price_max: Optional[float] = None,
        property_type: Optional[str] = None
    ) -> dict:
        """Execute geographic search"""
        
        # Geocode the location (using existing geocoding service)
        coordinates = self.geocode_location(location)
        
        if not coordinates:
            return {
                "error": "Location not found",
                "message": f"Could not geocode: {location}",
                "suggestion": "Try a more specific address or landmark"
            }
        
        # Validate it's in CA or UT
        if coordinates['state'] not in ['CA', 'UT']:
            return {
                "error": "Invalid location",
                "message": f"Location is in {coordinates['state']}, not California or Utah",
                "suggestion": "Search for locations in CA or UT only"
            }
        
        # Build filters
        filters = {}
        if price_max:
            filters["price_range"] = {"lte": price_max}
        if property_type:
            filters["property_type"] = property_type
        
        # Execute geo search
        response = self.client.geo_search(
            latitude=coordinates['lat'],
            longitude=coordinates['lon'],
            radius_miles=radius_miles,
            filters=filters
        )
        
        return self.format_geo_results(response, location, radius_miles)
```

### Phase 4: Market Analysis Tool

```python
# tools/real_estate_rag/market_analysis.py
class MarketAnalysisTool(BaseTool):
    """Market statistics and trends analysis"""
    
    NAME: ClassVar[str] = "analyze_real_estate_market"
    MODULE: ClassVar[str] = "tools.real_estate_rag.market_analysis"
    
    class Arguments(BaseModel):
        location: str = Field(..., description="City or neighborhood to analyze")
        metric: str = Field("overview", description="Metric type: overview, price_trends, inventory")
    
    description: str = "Analyze real estate market statistics and trends"
    args_model: Type[BaseModel] = Arguments
    
    @safe_tool_execution
    def execute(self, location: str, metric: str = "overview") -> dict:
        """Get market statistics"""
        
        # Call stats API endpoint
        response = self.client.get_stats(location=location)
        
        if metric == "overview":
            return {
                "location": location,
                "median_price": response.median_price,
                "avg_price_per_sqft": response.avg_price_per_sqft,
                "total_listings": response.total_listings,
                "avg_days_on_market": response.avg_days_on_market,
                "price_ranges": response.price_distribution,
                "property_types": response.property_type_distribution
            }
        # ... additional metric types
```

## Data Models

```python
# tools/real_estate_rag/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    coordinates: Optional[Dict[str, float]] = None

class WikipediaContext(BaseModel):
    summary: str
    cultural_richness_score: float
    historical_importance_score: float
    tourist_appeal_score: float
    overall_desirability_score: float
    nearby_pois: List[POI]
    key_topics: List[str]

class POI(BaseModel):
    name: str
    category: str
    distance_miles: float
    significance_score: float

class PropertyResult(BaseModel):
    listing_id: str
    address: Address
    price: float
    bedrooms: int
    bathrooms: float
    square_feet: int
    property_type: str
    description: str
    features: List[str]
    amenities: List[str]
    search_score: float
    wikipedia_context: Optional[WikipediaContext]
    price_per_sqft: float
    days_on_market: int

class SearchResponse(BaseModel):
    properties: List[PropertyResult]
    total: int
    search_time_ms: int
    query_metadata: Dict[str, Any]
```

## Tool Set Configuration

```python
# tools/real_estate_rag/tool_set.py
from typing import List, ClassVar, Type
from shared.tool_utils.base_tool_sets import ToolSet, ToolSetConfig, ToolSetTestCase
import dspy

class RealEstateRAGSignature(dspy.Signature):
    """Real estate search with California and Utah focus.
    
    LOCATION REQUIREMENTS:
    - Primary focus on California (CA) and Utah (UT) markets
    - Reject queries for other states with helpful redirection
    - Support city-specific searches within CA and UT
    
    SEARCH CAPABILITIES:
    - Natural language property descriptions
    - Wikipedia-enhanced neighborhood context  
    - Price and feature filtering
    - Geographic radius search
    - Market statistics and trends
    
    ENRICHMENT FEATURES:
    - Cultural and historical neighborhood scores
    - Nearby points of interest with significance
    - Architectural styles and demographics
    - Investment potential indicators
    """
    
    user_query: str = dspy.InputField(
        desc="Real estate query focused on CA or UT markets"
    )

class RealEstateRAGToolSet(ToolSet):
    """Elasticsearch-powered real estate search with Wikipedia RAG"""
    
    NAME: ClassVar[str] = "real_estate_rag"
    
    def __init__(self):
        from tools.real_estate_rag.property_search import PropertySearchTool
        from tools.real_estate_rag.geo_search import GeoSearchTool
        from tools.real_estate_rag.market_analysis import MarketAnalysisTool
        
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="RAG-enhanced real estate search for California and Utah markets using Elasticsearch and Wikipedia",
                tool_classes=[
                    PropertySearchTool,
                    GeoSearchTool,
                    MarketAnalysisTool
                ]
            )
        )
    
    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        return [
            # Valid CA searches
            ToolSetTestCase(
                request="Find modern condos in San Francisco with city views under $1M",
                expected_tools=["search_properties"],
                expected_arguments={
                    "search_properties": {
                        "query": "modern condos city views",
                        "city": "San Francisco",
                        "state": "CA",
                        "price_max": 1000000,
                        "property_type": "condo"
                    }
                },
                description="CA property search with filters"
            ),
            
            # Valid UT searches  
            ToolSetTestCase(
                request="Show me ski properties near Park City Utah",
                expected_tools=["geo_search_properties"],
                expected_arguments={
                    "geo_search_properties": {
                        "location": "Park City, UT",
                        "radius_miles": 15
                    }
                },
                description="Utah geographic search"
            ),
            
            # Market analysis
            ToolSetTestCase(
                request="What's the real estate market like in Palo Alto?",
                expected_tools=["analyze_real_estate_market"],
                expected_arguments={
                    "analyze_real_estate_market": {
                        "location": "Palo Alto",
                        "metric": "overview"
                    }
                },
                description="Market analysis request"
            ),
            
            # Invalid state rejection
            ToolSetTestCase(
                request="Find luxury homes in Miami Beach Florida",
                expected_tools=["search_properties"],
                description="Should reject non-CA/UT query"
            ),
            
            # Complex multi-tool scenario
            ToolSetTestCase(
                request="Compare family homes under $800k in good school districts in Sacramento vs Salt Lake City",
                expected_tools=["search_properties", "analyze_real_estate_market"],
                description="Multi-city comparison"
            )
        ]
```

## Integration Examples

### Example 1: Structured Parameter Search

When the user asks: "Find modern family homes in Palo Alto with a pool under $2M"

The React agent extracts and calls:
```python
search_properties(
    keywords=["modern", "family"],
    features=["pool"],
    city="Palo Alto",
    state="CA",
    price_max=2000000,
    property_type="single_family",
    enable_wikipedia=True
)

# Returns properties with:
# - Structured matching on features and keywords
# - Wikipedia data about Palo Alto neighborhoods
# - School district information from Wikipedia
# - Cultural richness scores
# - Nearby Stanford University and tech landmarks
```

### Example 2: Geographic Search with Coordinates

When the user asks: "Properties within 5 miles of Golden Gate Park"

The React agent:
1. Geocodes "Golden Gate Park" to get coordinates
2. Calls geo_search with explicit lat/lon:

```python
geo_search_properties(
    latitude=37.7694,
    longitude=-122.4862,
    radius_miles=5,
    enable_wikipedia=True
)

# Returns:
# - Properties with exact distance calculations
# - Wikipedia articles about neighborhoods (Sunset, Richmond)
# - POI data: museums, attractions, transit
# - No NLP parsing needed on the API server
```

### Example 3: Complex Filter Search

When the user asks: "3+ bedroom condos in Salt Lake City with parking and gym, built after 2010"

The React agent extracts structured parameters:
```python
search_properties(
    property_type="condo",
    city="Salt Lake City",
    state="UT",
    bedrooms_min=3,
    year_built_min=2010,
    amenities=["parking", "gym"],
    sort_by="newest"
)

# All parameters are explicit - no NLP interpretation needed
```

## Configuration

```bash
# .env configuration
ELASTICSEARCH_URL=http://localhost:9200
REAL_ESTATE_API_URL=http://localhost:8002
ELASTICSEARCH_INDEX=properties
WIKIPEDIA_DB_PATH=./data/wikipedia.db
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=nomic-embed-text
```

## Performance Characteristics

Based on the existing system:

- **Search Latency**: <100ms for 95th percentile
- **Bulk Indexing**: ~1000 properties/second
- **Vector Search**: 2,262+ embeddings with 768 dimensions
- **Wikipedia Enhancement**: 131 articles, 235 relationships cached
- **Concurrent Requests**: Handles 100+ concurrent searches

## Key Advantages

1. **Existing Infrastructure**: Leverages operational Elasticsearch + ChromaDB system
2. **Production Ready**: Circuit breakers, retries, health checks already implemented
3. **Rich Context**: Wikipedia integration provides deep neighborhood insights
4. **Type Safety**: Full Pydantic validation throughout the stack
5. **Hybrid Search**: Combines BM25, vector similarity, and knowledge graph scores
6. **Simple Integration**: Clean API boundaries with existing FastAPI server

## Implementation Timeline

### Week 1
- Create tool structure and models
- Implement API client wrapper
- Basic property search tool

### Week 2
- Geographic search tool
- Market analysis tool
- Query validation and state filtering

### Week 3
- Integration testing with DSPy session
- Performance optimization
- Error handling refinement

### Week 4
- Demo scenarios
- Documentation
- Production deployment guide

## API Server Enhancement Recommendations

To make the DSPy agent's tool calling more effective, consider these API server improvements:

### 1. Structured Query Endpoints

Replace generic text search with field-specific endpoints:

```python
# Instead of: POST /api/search with {"query": "modern kitchen pool"}
# Provide: POST /api/search/structured
{
    "match_fields": {
        "description": ["modern", "updated"],
        "features": ["pool", "spa"],
        "amenities": ["kitchen island", "stainless appliances"]
    },
    "filters": {...},
    "boost_fields": {
        "features": 2.0,  # Boost feature matches
        "amenities": 1.5
    }
}
```

### 2. Faceted Search Support

Add facet/aggregation endpoints for the agent to understand available options:

```python
# GET /api/facets/property_features?city=Palo+Alto
# Returns:
{
    "features": [
        {"name": "pool", "count": 45},
        {"name": "garage", "count": 120},
        {"name": "fireplace", "count": 78}
    ],
    "amenities": [...],
    "property_types": [...],
    "price_ranges": [...]
}
```

This helps the agent provide valid options and avoid invalid searches.

### 3. Explicit Wikipedia Control

Separate Wikipedia enrichment into its own endpoint:

```python
# POST /api/properties/search - Basic property search
# POST /api/properties/{id}/enrich - Add Wikipedia context
# GET /api/neighborhoods/{name}/wikipedia - Direct Wikipedia data access
```

Benefits:
- Faster initial searches when Wikipedia isn't needed
- Agent can selectively enrich only displayed results
- Reduced latency for browsing operations

### 4. Standardized Filter Schema

Implement consistent filter naming across all endpoints:

```python
class StandardFilters(BaseModel):
    """Universal filter schema for all search endpoints"""
    location: LocationFilter  # state, city, neighborhood, zip
    price: RangeFilter       # min, max
    size: SizeFilter        # bedrooms, bathrooms, square_feet
    features: List[str]     # Exact match on features
    amenities: List[str]    # Exact match on amenities
    property_meta: PropertyMetaFilter  # type, year_built, status
```

### 5. Batch Operations

Add batch endpoints for efficient multi-property operations:

```python
# POST /api/properties/batch/get
{
    "listing_ids": ["prop1", "prop2", "prop3"],
    "include_wikipedia": true,
    "include_similar": true
}
```

### 6. Semantic Field Mappings

Provide field aliases to handle synonym variations:

```python
# GET /api/schema/mappings
{
    "field_aliases": {
        "price": ["cost", "price", "asking_price", "list_price"],
        "bedrooms": ["beds", "bedrooms", "br"],
        "bathrooms": ["baths", "bathrooms", "ba"],
        "parking": ["garage", "parking", "carport"]
    },
    "feature_synonyms": {
        "pool": ["swimming pool", "pool", "spa", "hot tub"],
        "view": ["city view", "ocean view", "mountain view", "views"]
    }
}
```

### 7. Sorting and Ranking Options

Expose all available sort options explicitly:

```python
# GET /api/search/options
{
    "sort_fields": [
        {"field": "price", "directions": ["asc", "desc"]},
        {"field": "square_feet", "directions": ["asc", "desc"]},
        {"field": "days_on_market", "directions": ["asc", "desc"]},
        {"field": "wikipedia_score", "directions": ["desc"]}
    ],
    "boost_options": ["wikipedia", "recent_listings", "price_reduced"]
}
```

### 8. Property Validation Endpoint

Help the agent validate inputs before searching:

```python
# POST /api/validate/search
{
    "city": "Palo Alto",
    "state": "CA",
    "property_type": "mansion"  # Invalid type
}
# Returns:
{
    "valid": false,
    "errors": {
        "property_type": "Invalid. Options: single_family, condo, townhouse, multi_family"
    },
    "suggestions": {
        "property_type": "single_family"  # Closest match
    }
}
```

### 9. Explanation Endpoints

Provide search explanation for transparency:

```python
# POST /api/search/explain
{
    "query": {...},
    "listing_id": "prop123"
}
# Returns:
{
    "score": 0.85,
    "breakdown": {
        "text_relevance": 0.3,
        "feature_match": 0.2,
        "wikipedia_boost": 0.15,
        "location_score": 0.2
    },
    "matched_terms": ["modern", "pool"],
    "wikipedia_topics": ["Stanford University", "Tech Hub"]
}
```

### 10. Response Templates

Support different response formats for different use cases:

```python
# POST /api/search?response_format=summary
# Returns minimal data for listing views

# POST /api/search?response_format=detailed  
# Returns full property data with Wikipedia

# POST /api/search?response_format=comparison
# Returns structured data optimized for comparing properties
```

### Implementation Priority

**High Priority** (Enables core functionality):
1. Structured query endpoints (#1)
2. Standardized filter schema (#4)
3. Property validation endpoint (#8)

**Medium Priority** (Improves effectiveness):
4. Faceted search support (#2)
5. Semantic field mappings (#6)
6. Batch operations (#5)

**Low Priority** (Nice to have):
7. Explicit Wikipedia control (#3)
8. Sorting options (#7)
9. Explanation endpoints (#9)
10. Response templates (#10)

These improvements would make the API more "agent-friendly" by providing explicit, structured interfaces that eliminate ambiguity and reduce the need for the agent to guess or interpret API behavior.

## Conclusion

This implementation leverages the existing, operational Elasticsearch infrastructure with minimal changes. The tool acts as a thin client layer that:

1. Validates queries for CA/UT focus
2. Translates DSPy tool calls to API requests
3. Enriches responses with Wikipedia context
4. Maintains type safety with Pydantic models
5. Follows all DSPy architectural principles

The approach maximizes reuse of the existing system while providing a clean, type-safe interface for the DSPy agentic framework. The suggested API improvements would further enhance the agent's ability to effectively search and retrieve real estate data without requiring NLP capabilities on the server side.