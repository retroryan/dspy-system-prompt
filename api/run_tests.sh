#!/bin/bash
#
# Run API tests
#

echo "=========================================="
echo "Running API Test Suite"
echo "=========================================="
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  API server not running!"
    echo "   Please start the server first:"
    echo "   ./run_api.sh"
    echo ""
    exit 1
fi

echo "✓ API server is running"
echo ""

# Run tests with pytest
echo "Running tests..."
echo "=========================================="

# Basic tests (fast)
if [ "$1" == "fast" ]; then
    echo "Running fast tests only..."
    poetry run pytest api/tests -v -m "not slow"
elif [ "$1" == "integration" ]; then
    echo "Running integration tests..."
    poetry run pytest api/tests -v -m "integration"
elif [ "$1" == "coverage" ]; then
    echo "Running tests with coverage..."
    poetry run pytest api/tests -v --cov=api --cov-report=term-missing
else
    echo "Running all tests..."
    poetry run pytest api/tests -v
fi

echo ""
echo "=========================================="
echo "Test run complete!"
echo "=========================================="