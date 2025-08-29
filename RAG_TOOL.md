# Real Estate RAG Tool Proposal

## Executive Summary

This proposal outlines the design and implementation of a RAG (Retrieval-Augmented Generation) tool for the DSPy agentic loop system that interfaces with an existing Elasticsearch-indexed real estate database. The tool will provide sophisticated real estate search capabilities with Wikipedia-enhanced context while maintaining separation between the data ingestion system and the search interface.

## Architecture Overview

### Core Design Principles

1. **Separation of Concerns**: The real estate indexing system remains independent; this tool acts as a client
2. **API-Based Integration**: Clean interface via HTTP API calls to Elasticsearch/Neo4j backend
3. **Query Categorization**: Pre-filter queries to only accept California and Utah real estate queries
4. **Wikipedia Enhancement**: Leverage existing Wikipedia integration for enriched context
5. **Type Safety**: Full Pydantic models for request/response validation
6. **Simplicity**: High-quality proof-of-concept, not production-grade complexity

### System Components

```
DSPy Agent Session
       ↓
Real Estate RAG Tool
       ↓
Query Categorizer → API Gateway → Elasticsearch/Neo4j
                                        ↓
                                  Wikipedia Context
```

## Implementation Plan

### Phase 1: Tool Structure

Create new tool directory: `tools/real_estate_rag/`

```
tools/real_estate_rag/
├── __init__.py
├── tool_set.py              # Tool set configuration
├── property_search.py       # Main search tool
├── neighborhood_insights.py # Neighborhood context tool
├── market_analysis.py       # Market trends tool
├── models.py               # Pydantic models
├── api_client.py           # HTTP client for Elasticsearch
└── query_classifier.py     # CA/UT filter logic
```

### Phase 2: Core Components

#### 1. Query Classifier (`query_classifier.py`)

```python
class QueryClassifier:
    """Classifies queries as valid real estate searches for CA/UT"""
    
    VALID_STATES = ["california", "ca", "utah", "ut"]
    
    CALIFORNIA_CITIES = [
        "los angeles", "san francisco", "san diego", "san jose",
        "sacramento", "oakland", "berkeley", "palo alto", "santa monica"
    ]
    
    UTAH_CITIES = [
        "salt lake city", "provo", "park city", "ogden", 
        "st george", "logan", "sandy", "orem"
    ]
    
    def classify(self, query: str) -> QueryClassification:
        """
        Determines if query is:
        1. Valid real estate query for CA/UT
        2. Which state/city is being targeted
        3. Query intent (search, analysis, comparison)
        """
```

#### 2. API Client (`api_client.py`)

```python
class RealEstateAPIClient:
    """HTTP client for Elasticsearch/Neo4j backend"""
    
    def __init__(self, base_url: str = "http://localhost:9200"):
        self.base_url = base_url
        self.session = requests.Session()
    
    async def vector_search(
        self, 
        query_embedding: List[float],
        filters: SearchFilters
    ) -> List[PropertyResult]:
        """Execute vector similarity search"""
        
    async def get_wikipedia_context(
        self,
        neighborhood: str,
        context_type: str = "all"
    ) -> WikipediaContext:
        """Fetch Wikipedia enrichment for neighborhoods"""
```

#### 3. Main Search Tool (`property_search.py`)

```python
class PropertySearchTool(BaseTool):
    """RAG-enhanced real estate property search"""
    
    NAME: ClassVar[str] = "real_estate_search"
    MODULE: ClassVar[str] = "tools.real_estate_rag.property_search"
    
    class Arguments(BaseModel):
        query: str = Field(..., description="Natural language search query")
        city: Optional[str] = Field(None, description="City filter (CA or UT)")
        price_min: Optional[float] = Field(None, description="Minimum price")
        price_max: Optional[float] = Field(None, description="Maximum price")
        bedrooms_min: Optional[int] = Field(None, description="Minimum bedrooms")
        include_wikipedia: bool = Field(True, description="Include Wikipedia context")
    
    @safe_tool_execution
    def execute(self, **kwargs) -> dict:
        # 1. Classify query
        classification = self.classifier.classify(kwargs['query'])
        if not classification.is_valid:
            return {
                "error": "Query must be about California or Utah real estate",
                "suggestion": "Try searching for properties in cities like San Francisco, Los Angeles, Salt Lake City, or Park City"
            }
        
        # 2. Generate embedding for semantic search
        query_embedding = self.generate_embedding(kwargs['query'])
        
        # 3. Execute hybrid search (vector + graph)
        search_results = self.api_client.vector_search(
            query_embedding,
            filters=self.build_filters(kwargs, classification)
        )
        
        # 4. Enhance with Wikipedia context if requested
        if kwargs.get('include_wikipedia', True):
            for result in search_results:
                wiki_context = self.api_client.get_wikipedia_context(
                    result.neighborhood
                )
                result.wikipedia_insights = self.synthesize_insights(
                    result, wiki_context
                )
        
        # 5. Format response with RAG synthesis
        return self.format_rag_response(search_results, kwargs['query'])
```

### Phase 3: Data Models (`models.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class PropertyType(str, Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"

class PropertyResult(BaseModel):
    """Enhanced property search result"""
    listing_id: str
    address: Optional[str]
    city: str
    state: str
    neighborhood: str
    price: float
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    property_type: Optional[PropertyType]
    description: str
    
    # Vector search scores
    vector_score: float
    graph_score: float
    combined_score: float
    
    # Wikipedia enhancement
    wikipedia_insights: Optional['WikipediaInsights']
    
    # Similar properties for comparison
    similar_properties: List[str]
    features: List[str]

class WikipediaInsights(BaseModel):
    """Wikipedia-derived neighborhood context"""
    neighborhood_overview: str
    cultural_highlights: List[str]
    nearby_landmarks: List[Dict[str, str]]
    lifestyle_tags: List[str]
    transit_options: List[str]
    demographic_notes: Optional[str]
    investment_insights: Optional[str]

class QueryClassification(BaseModel):
    """Query classification result"""
    is_valid: bool
    detected_state: Optional[str]
    detected_cities: List[str]
    query_intent: str  # search, compare, analyze, invest
    property_features: List[str]
    rejection_reason: Optional[str]
```

### Phase 4: Tool Set Configuration (`tool_set.py`)

```python
class RealEstateRAGSignature(dspy.Signature):
    """Real estate search with location validation.
    
    IMPORTANT LOCATION REQUIREMENTS:
    - Only accept queries about California (CA) or Utah (UT) properties
    - Reject queries about other states or countries
    - Be explicit about location requirements in responses
    
    SEARCH CAPABILITIES:
    - Natural language property search
    - Wikipedia-enhanced neighborhood insights
    - Market analysis and trends
    - Investment recommendations
    - Lifestyle matching
    """
    
    user_query: str = dspy.InputField(
        desc="Real estate query that must target CA or UT markets"
    )

class RealEstateRAGToolSet(ToolSet):
    """RAG-enhanced real estate search tools"""
    
    NAME: ClassVar[str] = "real_estate_rag"
    
    def __init__(self):
        from tools.real_estate_rag.property_search import PropertySearchTool
        from tools.real_estate_rag.neighborhood_insights import NeighborhoodInsightsTool
        from tools.real_estate_rag.market_analysis import MarketAnalysisTool
        
        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="RAG-enhanced real estate search for California and Utah markets",
                tool_classes=[
                    PropertySearchTool,
                    NeighborhoodInsightsTool,
                    MarketAnalysisTool
                ]
            )
        )
```

## API Design

### Backend Service (Separate Process)

The backend service will run as a FastAPI application providing:

```python
# api_server.py (in real_estate_ai_search directory)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Real Estate RAG API")

@app.post("/api/v1/search")
async def search_properties(request: SearchRequest):
    """Vector + graph hybrid search"""
    
@app.get("/api/v1/neighborhood/{name}/wikipedia")
async def get_neighborhood_wikipedia(name: str):
    """Get Wikipedia context for neighborhood"""
    
@app.post("/api/v1/classify")
async def classify_query(query: str):
    """Classify if query is valid CA/UT real estate"""

# Run with: uvicorn api_server:app --port 8100
```

## Integration Examples

### Example 1: Basic Property Search

```python
session = AgentSession("real_estate_rag")
result = session.query("Find me a modern condo in San Francisco with city views under $800k")

# Tool execution:
# 1. Classifies as valid CA query
# 2. Searches properties with vector similarity
# 3. Enhances with Wikipedia data about neighborhoods
# 4. Returns ranked results with context
```

### Example 2: Query Rejection

```python
result = session.query("Show me penthouses in Manhattan")

# Response:
# "I can only search for properties in California and Utah. 
#  Would you like to search for luxury properties in 
#  San Francisco or Salt Lake City instead?"
```

### Example 3: Wikipedia-Enhanced Context

```python
result = session.query("Family home near good schools in Palo Alto")

# Returns properties with enriched context:
# - School district rankings from Wikipedia
# - Notable tech companies nearby
# - Stanford University proximity
# - Cultural attractions and parks
```

## Test Cases

```python
@classmethod
def get_test_cases(cls) -> List[ToolTestCase]:
    return [
        ToolTestCase(
            request="Find luxury homes in Beverly Hills",
            expected_tools=["real_estate_search"],
            description="Valid CA search"
        ),
        ToolTestCase(
            request="Search for ski properties in Park City Utah",
            expected_tools=["real_estate_search"],
            description="Valid UT search"
        ),
        ToolTestCase(
            request="Show me condos in Miami Beach",
            expected_tools=[],
            description="Invalid location - should reject"
        ),
        ToolTestCase(
            request="Compare neighborhoods in San Francisco for families",
            expected_tools=["neighborhood_insights"],
            description="Neighborhood analysis"
        ),
        ToolTestCase(
            request="Investment opportunities in Salt Lake City real estate",
            expected_tools=["market_analysis", "real_estate_search"],
            description="Market analysis query"
        )
    ]
```

## Configuration

### Environment Variables

```bash
# .env additions
REAL_ESTATE_API_URL=http://localhost:8100
REAL_ESTATE_API_KEY=optional_key_for_future
ELASTICSEARCH_URL=http://localhost:9200
NEO4J_URI=bolt://localhost:7687
```

## Implementation Timeline

### Week 1: Foundation
- Set up tool structure and models
- Implement query classifier
- Create API client with mock responses

### Week 2: Core Functionality  
- Implement property search tool
- Add Wikipedia enhancement logic
- Create backend API server

### Week 3: Enhanced Features
- Add neighborhood insights tool
- Implement market analysis tool
- Comprehensive test suite

### Week 4: Integration & Polish
- Full integration testing
- Demo scenarios
- Documentation and examples

## Benefits

1. **Rich Context**: Wikipedia integration provides cultural, historical, and lifestyle context
2. **Smart Filtering**: Automatic CA/UT validation prevents irrelevant searches
3. **Type Safety**: Full Pydantic validation throughout
4. **Scalable Design**: API-based architecture allows independent scaling
5. **Clean Separation**: Data ingestion and search remain independent
6. **DSPy Native**: Follows all DSPy patterns and best practices

## Potential Enhancements (Future)

1. **Caching Layer**: Redis cache for frequently searched neighborhoods
2. **User Preferences**: Learn from session history for personalized results  
3. **Image Integration**: Property images with descriptions
4. **Virtual Tours**: Links to 3D tours when available
5. **Market Predictions**: Time-series analysis for price trends
6. **Commute Analysis**: Integration with transit APIs
7. **School Data**: Direct integration with school rating APIs
8. **Crime Statistics**: Safety scores from public data

## Conclusion

This RAG tool design provides a clean, type-safe interface between the DSPy agentic system and the real estate search infrastructure. By maintaining separation of concerns and using API-based integration, we achieve flexibility while keeping the implementation simple and focused. The Wikipedia enhancement adds significant value by transforming static property data into rich, contextual narratives that help users make informed decisions.

The query categorization ensures the system remains focused on its core markets (California and Utah), providing high-quality results rather than attempting to cover all locations with lower quality. This focused approach aligns with the DSPy philosophy of doing one thing well rather than many things poorly.