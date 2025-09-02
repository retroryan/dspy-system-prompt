#!/bin/bash
#
# Run integration tests against the API server
#

echo "=========================================="
echo "API Integration Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if server is already running
check_server() {
    curl -s http://localhost:8000/health > /dev/null 2>&1
    return $?
}

# Function to start server
start_server() {
    echo "🚀 Starting API server in background..."
    
    # Start server in background and save PID
    poetry run uvicorn api.main:app --host 0.0.0.0 --port 8000 > /tmp/api_server.log 2>&1 &
    SERVER_PID=$!
    echo "   Server PID: $SERVER_PID"
    
    # Wait for server to be ready
    echo "⏳ Waiting for server to be ready..."
    for i in {1..30}; do
        if check_server; then
            echo -e "${GREEN}✓ Server is ready!${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}✗ Server failed to start${NC}"
    echo "   Check /tmp/api_server.log for details"
    return 1
}

# Main execution
SERVER_STARTED_BY_SCRIPT=false

# Check if server is already running
if check_server; then
    echo -e "${GREEN}✓ API server already running${NC}"
else
    # Start the server
    if start_server; then
        SERVER_STARTED_BY_SCRIPT=true
    else
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Running Integration Tests"
echo "=========================================="
echo ""

# Run the integration tests
if [ "$1" == "verbose" ]; then
    echo "Running tests with verbose output..."
    poetry run python -m pytest api/integration_tests -v -s
elif [ "$1" == "quick" ]; then
    echo "Running quick tests only..."
    poetry run python -m pytest api/integration_tests -v -m "not slow"
elif [ "$1" == "workflows" ]; then
    echo "Running workflow tests..."
    poetry run python -m pytest api/integration_tests -v -m "workflow"
else
    echo "Running all integration tests..."
    poetry run python -m pytest api/integration_tests -v
fi

TEST_RESULT=$?

echo ""
echo "=========================================="

# Clean up if we started the server
if [ "$SERVER_STARTED_BY_SCRIPT" = true ]; then
    echo "🧹 Cleaning up..."
    echo "   Stopping API server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null
    sleep 1
    
    # Force kill if still running
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        kill -9 $SERVER_PID 2>/dev/null
    fi
    
    echo -e "${GREEN}✓ Server stopped${NC}"
fi

# Report test results
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ All integration tests passed!${NC}"
else
    echo -e "${RED}❌ Some integration tests failed${NC}"
    
    if [ "$SERVER_STARTED_BY_SCRIPT" = true ]; then
        echo ""
        echo "Server logs from /tmp/api_server.log:"
        echo "--------------------------------------"
        tail -20 /tmp/api_server.log
    fi
fi

echo "=========================================="
echo ""

exit $TEST_RESULT