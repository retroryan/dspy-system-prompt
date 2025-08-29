# API Curl Examples

This document provides curl command examples for all API endpoints.

## Quick Reference

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **Session-based**: Most operations require a session ID

## Health & Metrics

### Check Health
```bash
curl -X GET http://localhost:8000/health
```

### Get Metrics
```bash
curl -X GET http://localhost:8000/metrics
```

## Tool Sets

### List All Tool Sets
```bash
curl -X GET http://localhost:8000/tool-sets
```

### Get Specific Tool Set
```bash
curl -X GET http://localhost:8000/tool-sets/ecommerce
```

## Session Management

### Create Session
```bash
# Basic session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "tool_set": "ecommerce",
    "user_id": "demo_user"
  }'

# With custom configuration
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "tool_set": "agriculture",
    "user_id": "farmer_user",
    "config": {
      "max_messages": 100,
      "summarize_removed": true
    }
  }'
```

### Get Session Info
```bash
# Replace SESSION_ID with actual session ID
curl -X GET http://localhost:8000/sessions/SESSION_ID
```

### Reset Session
```bash
curl -X POST http://localhost:8000/sessions/SESSION_ID/reset
```

### Delete Session
```bash
curl -X DELETE http://localhost:8000/sessions/SESSION_ID
```

### Get User Sessions
```bash
curl -X GET http://localhost:8000/sessions/user/demo_user
```

## Query Execution

### Execute Query
```bash
# Simple query
curl -X POST http://localhost:8000/sessions/SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me my recent orders"
  }'

# With custom iterations
curl -X POST http://localhost:8000/sessions/SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find the best laptop under $1000",
    "max_iterations": 8
  }'
```

## Complete Workflow Examples

### E-commerce Shopping Flow
```bash
# 1. Create session
SESSION_ID=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "tool_set": "ecommerce",
    "user_id": "shopper"
  }' | jq -r '.session_id')

echo "Session created: $SESSION_ID"

# 2. Query for products
curl -X POST http://localhost:8000/sessions/$SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me gaming keyboards under $200"
  }' | jq '.answer'

# 3. Add to cart
curl -X POST http://localhost:8000/sessions/$SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Add the cheapest gaming keyboard to my cart"
  }' | jq '.answer'

# 4. Checkout
curl -X POST http://localhost:8000/sessions/$SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Complete checkout with express shipping"
  }' | jq '.answer'

# 5. Clean up
curl -X DELETE http://localhost:8000/sessions/$SESSION_ID
```

### Agriculture Analysis Flow
```bash
# 1. Create session
SESSION_ID=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "tool_set": "agriculture",
    "user_id": "farmer"
  }' | jq -r '.session_id')

# 2. Weather check
curl -X POST http://localhost:8000/sessions/$SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the weather forecast for this week?"
  }' | jq '.'

# 3. Soil analysis
curl -X POST http://localhost:8000/sessions/$SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Check soil conditions for planting corn"
  }' | jq '.'

# 4. Get recommendations
curl -X POST http://localhost:8000/sessions/$SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What crops should I plant based on current conditions?"
  }' | jq '.'

# 5. Clean up
curl -X DELETE http://localhost:8000/sessions/$SESSION_ID
```

## Error Handling Examples

### Invalid Tool Set
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "tool_set": "invalid",
    "user_id": "test"
  }'
# Returns 404 with error details
```

### Session Not Found
```bash
curl -X GET http://localhost:8000/sessions/non-existent-id
# Returns 404 with SESSION_NOT_FOUND error
```

### Invalid Query
```bash
curl -X POST http://localhost:8000/sessions/SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "",
    "max_iterations": 20
  }'
# Returns 400 validation error
```

## Using with jq for Pretty Output

### Pretty print JSON responses
```bash
curl -X GET http://localhost:8000/health | jq '.'
```

### Extract specific fields
```bash
# Get just the session ID
curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"tool_set": "ecommerce", "user_id": "test"}' | jq -r '.session_id'

# Get query answer only
curl -s -X POST http://localhost:8000/sessions/SESSION_ID/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' | jq -r '.answer'
```

### Filter tool sets by name
```bash
curl -s -X GET http://localhost:8000/tool-sets | jq '.[] | select(.name=="ecommerce")'
```

## Debugging Tips

### Verbose output
```bash
curl -v -X GET http://localhost:8000/health
```

### Save response to file
```bash
curl -X GET http://localhost:8000/tool-sets -o tool-sets.json
```

### Include response headers
```bash
curl -i -X GET http://localhost:8000/health
```

### Time the request
```bash
curl -w "\nTime: %{time_total}s\n" -X GET http://localhost:8000/health
```