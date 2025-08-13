# Agentic Loop Architecture

## React → Extract → Observe Pattern

```mermaid
flowchart TD
    Start([User Query]) --> Controller[Demo Controller<br/>demo_react_agent.py]
    
    Controller --> ReactLoop{React Loop<br/>max_iterations: 5}
    
    ReactLoop --> React[React Agent<br/>DSPy Reasoning]
    React --> LLM1[LLM]
    LLM1 --> |"next_thought<br/>next_tool_name<br/>next_tool_args"| ToolExec[Tool Execution<br/>External Control]
    
    ToolExec --> |Tool Result| LLM2[LLM]
    LLM2 --> Trajectory[Update Trajectory<br/>thoughts, actions, observations]
    
    Trajectory --> CheckComplete{Task<br/>Complete?}
    CheckComplete -->|No| ReactLoop
    CheckComplete -->|Yes| Extract[Extract Agent<br/>DSPy Synthesis]
    
    Extract --> LLM3[LLM]
    LLM3 --> |"reasoning<br/>final_answer"| Response([User Response])
    
    %% Styling
    classDef controller fill:#e1f5fe,stroke:#0288d1
    classDef agent fill:#f3e5f5,stroke:#7b1fa2
    classDef execution fill:#fff3e0,stroke:#f57c00
    classDef data fill:#e8f5e9,stroke:#388e3c
    classDef llm fill:#fff9c4,stroke:#f9a825
    
    class Controller,ReactLoop controller
    class React,Extract agent
    class ToolExec execution
    class Trajectory,CheckComplete data
    class LLM1,LLM2,LLM3 llm
```

## Key Components

### 1. Demo Controller (`demo_react_agent.py`)
- Maintains external control over the entire loop
- Manages iteration limits and timeouts
- Handles tool registration and execution

### 2. React Agent (`react_agent.py`)
- Uses `dspy.Predict` for reasoning
- Selects tools based on task and trajectory
- Returns structured output with next action

### 3. Tool Execution
- Controller executes tools externally
- Maintains full error handling and retry logic
- Updates trajectory with observations

### 4. Extract Agent (`extract_agent.py`)
- Uses `dspy.ChainOfThought` for synthesis
- Analyzes complete trajectory
- Produces final answer from all observations

### 5. Trajectory State
- Stores all thoughts, actions, and observations
- Provides full observability of the process
- Used by both React and Extract agents

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Controller
    participant ReactAgent
    participant Tools
    participant ExtractAgent
    
    User->>Controller: Query
    Controller->>ReactAgent: Initial task
    
    loop React Loop (max 5 iterations)
        ReactAgent->>Controller: next_thought, tool_name, tool_args
        Controller->>Tools: Execute tool
        Tools->>Controller: Tool result
        Controller->>Controller: Update trajectory
        Controller->>ReactAgent: Updated trajectory
    end
    
    Controller->>ExtractAgent: Complete trajectory
    ExtractAgent->>Controller: Final answer
    Controller->>User: Response
```

## Tool Set Architecture

```mermaid
graph LR
    Registry[Tool Registry] --> Agriculture[Agriculture Tools]
    Registry --> Ecommerce[Ecommerce Tools]
    Registry --> Events[Events Tools]
    
    Agriculture --> Weather[Weather Current]
    Agriculture --> Forecast[Weather Forecast]
    Agriculture --> Historical[Weather Historical]
    
    Ecommerce --> Search[Product Search]
    Ecommerce --> Cart[Shopping Cart]
    Ecommerce --> Orders[Order Management]
    
    Events --> Find[Find Events]
    Events --> Create[Create Event]
    Events --> Cancel[Cancel Event]
```