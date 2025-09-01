#!/bin/bash
#
# Run the Agentic Loop API server and Frontend
#

echo "=========================================="
echo "Starting DSPy Demo Application"
echo "=========================================="
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install it first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

# Install backend dependencies if needed
echo "📦 Checking backend dependencies..."
poetry install --quiet

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "   Installing frontend dependencies..."
    npm install
fi
cd ..

# Set default environment variables if not already set
export API_PORT="${API_PORT:-3010}"
export API_HOST="${API_HOST:-0.0.0.0}"
export DEBUG_MODE="${DEBUG_MODE:-false}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export FRONTEND_PORT="${FRONTEND_PORT:-3000}"

# Print configuration
echo ""
echo "Configuration:"
echo "  - API Host: $API_HOST"
echo "  - API Port: $API_PORT"
echo "  - Frontend Port: $FRONTEND_PORT"
echo "  - Debug: $DEBUG_MODE"
echo "  - Log Level: $LOG_LEVEL"
echo "  - Logs Directory: ./logs/"
echo ""
echo "=========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set trap to cleanup on exit
trap cleanup INT TERM

# Start API server in background
echo "🚀 Starting API server..."
echo "   Documentation: http://localhost:$API_PORT/docs"
echo "   Health check:  http://localhost:$API_PORT/health"
echo "   API logs:      ./logs/api.log"
echo ""
poetry run uvicorn api.main:app --host $API_HOST --port $API_PORT --reload > logs/api.log 2>&1 &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API server to start..."
for i in {1..30}; do
    if curl -s http://localhost:$API_PORT/health > /dev/null 2>&1; then
        echo "✅ API server is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ API server failed to start. Check logs/api.log for details."
        exit 1
    fi
done

# Start frontend server in background
echo ""
echo "🚀 Starting frontend server..."
echo "   Application:   http://localhost:$FRONTEND_PORT"
echo "   Frontend logs: ./logs/frontend.log"
echo ""
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to be ready
echo "⏳ Waiting for frontend server to start..."
for i in {1..30}; do
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        echo "✅ Frontend server is ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Frontend server failed to start. Check logs/frontend.log for details."
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "✨ Application is running!"
echo ""
echo "  🌐 Frontend:     http://localhost:$FRONTEND_PORT"
echo "  📚 API Docs:     http://localhost:$API_PORT/docs"
echo "  🔍 Health Check: http://localhost:$API_PORT/health"
echo ""
echo "  📝 Logs:"
echo "     - API:      ./logs/api.log"
echo "     - Frontend: ./logs/frontend.log"
echo ""
echo "  Press Ctrl+C to stop all servers"
echo "=========================================="
echo ""

# Keep script running and show logs
tail -f logs/api.log logs/frontend.log