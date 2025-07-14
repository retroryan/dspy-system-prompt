# Tool Signature Architecture - Two-Signature Pattern Implementation

## Primary Goals

1. **Two-Signature Pattern**: Each tool set provides separate React and Extract signatures
2. **Clean Separation of Concerns**: React signatures contain tool execution requirements, Extract signatures contain synthesis fields
3. **Registry Integration**: ToolRegistry retrieves signatures from registered tool sets
4. **Weather Tool Focus**: Implementation focuses solely on weather tools - no backward compatibility layers
5. **DSPy Native**: Follows exact patterns from dspy.ReAct implementation

## Architectural Design

### Core Concept

Each tool set defines two distinct DSPy signatures:

1. **React Signature**: Domain-specific requirements for tool execution (coordinate extraction, precision requirements)
2. **Extract Signature**: Input/output fields for final answer synthesis (query field, analysis field)

### Signature Flow

The ReactAgent receives the React signature and augments it with tool instructions during initialization.
The ExtractAgent receives the Extract signature for clean synthesis without tool confusion.

## Implementation Components

### 1. ToolSet Base Class Updates

The ToolSet base class needs two new class methods:
- `get_react_signature()` - Returns the React signature for tool execution requirements
- `get_extract_signature()` - Returns the Extract signature for synthesis

Both methods return signature classes or None if the tool set uses default behavior.

### 2. Weather Signatures

#### WeatherReactSignature
- Contains coordinate extraction instructions and examples
- Defines weather precision requirements (elevation, microclimates, coastal effects)
- Single input field: weather_query
- NO output fields (those are added by ReactAgent)

#### WeatherExtractSignature
- Clean synthesis signature without tool instructions
- Input field: weather_query (original user query)
- Output field: weather_analysis (comprehensive response)

### 3. WeatherToolSet Updates

The WeatherToolSet implements both signature methods:
- Returns WeatherReactSignature for React requirements
- Returns WeatherExtractSignature for synthesis
- Removes old system_prompt approach

### 4. ToolRegistry Updates

The ToolRegistry exposes signature access:
- `get_react_signature()` - Retrieves React signature from registered tool set
- `get_extract_signature()` - Retrieves Extract signature from registered tool set
- Returns None if no tool set is registered

### 5. Agent Integration

The agent initialization flow:
1. Register WeatherToolSet with ToolRegistry
2. Retrieve signatures from registry
3. Pass appropriate signature to each agent
4. ReactAgent augments with tool instructions
5. ExtractAgent uses clean signature for synthesis

## Signature Flow Through the System

### ReactAgent Processing

The ReactAgent receives WeatherReactSignature and:
1. Extracts input fields from the signature
2. Preserves coordinate extraction instructions
3. Adds tool selection instructions dynamically
4. Appends trajectory and tool output fields

### ExtractAgent Processing

The ExtractAgent receives WeatherExtractSignature and:
1. Uses complete signature (input + output fields)
2. Has NO tool instructions to avoid confusion
3. Adds trajectory field for synthesis context
4. Focuses purely on domain synthesis

## Tool Updates Required

### BaseTool Changes

Tools must return formatted strings instead of dictionaries:
- Execute method returns string type
- String output suitable for trajectory display
- Error cases also return formatted error strings

### ToolRegistry Changes

The execute_tool method handles string outputs:
- Validates tool exists
- Executes tool and receives string result
- Wraps string in ToolExecutionResult
- Maintains execution metadata

### Weather Tool Modifications

Each weather tool needs updates:
- Accept coordinate parameters directly
- Format API responses as readable strings
- Include relevant weather details in output
- Handle errors with descriptive messages

## Weather Query Processing Example

When a user asks "What's the weather forecast for New York City?":

### ReactAgent Phase
1. Receives weather_query with location reference
2. Uses coordinate extraction instructions from WeatherReactSignature
3. Extracts coordinates: 40.7128, -74.0060
4. Calls weather tool with precise coordinates
5. Receives formatted string response
6. Stores observation in trajectory

### ExtractAgent Phase
1. Receives original query and trajectory
2. Uses WeatherExtractSignature for synthesis
3. Has no tool instructions to cause confusion
4. Synthesizes user-friendly response
5. Returns comprehensive weather analysis

## Key Design Benefits

### Clean Separation
- React signatures contain only execution requirements
- Extract signatures focus on synthesis fields
- No mixing of concerns between modules

### Flexibility
- Tool sets provide signatures only when needed
- Default behavior for simple tool sets
- Weather tools demonstrate advanced pattern

### Registry Integration
- Central signature access point
- Clean API for agent initialization
- Tool set registration includes signatures

## Implementation Progress

### Completed
- ✓ Architectural design finalized
- ✓ Two-signature pattern defined
- ✓ Weather tool requirements documented
- ✓ ToolSet base class updated with get_react_signature and get_extract_signature methods
- ✓ WeatherReactSignature implemented with coordinate extraction instructions
- ✓ WeatherExtractSignature implemented for synthesis
- ✓ WeatherToolSet updated to return both signatures
- ✓ ToolRegistry updated to expose signature methods
- ✓ BaseTool updated to return strings instead of dicts
- ✓ All weather tools updated to return formatted strings:
  - WeatherForecastTool - Returns formatted forecast with daily summaries
  - AgriculturalWeatherTool - Returns soil conditions and agricultural data
  - HistoricalWeatherTool - Returns historical weather with period summaries

### Ready for Testing
The implementation is complete and ready for integration testing:
1. ReactAgent can retrieve WeatherReactSignature from registry
2. ExtractAgent can retrieve WeatherExtractSignature from registry
3. Weather tools return human-readable strings for trajectory
4. Coordinate extraction instructions are in place
5. Clean separation between tool requirements and synthesis