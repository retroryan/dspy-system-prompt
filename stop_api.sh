#!/bin/bash
#
# Stop the Agentic Loop API server and Frontend
#

echo "=========================================="
echo "Stopping DSPy Demo Application"
echo "=========================================="
echo ""

# Set default ports if not already set
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

# Function to find and kill process on a specific port
kill_process_on_port() {
    local port=$1
    local service_name=$2
    
    # Find process ID using the port
    local pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pid" ]; then
        echo "🛑 Stopping $service_name (PID: $pid) on port $port..."
        kill $pid 2>/dev/null
        
        # Wait for process to terminate
        for i in {1..10}; do
            if ! lsof -ti:$port > /dev/null 2>&1; then
                echo "✅ $service_name stopped successfully"
                return 0
            fi
            sleep 0.5
        done
        
        # Force kill if still running
        if lsof -ti:$port > /dev/null 2>&1; then
            echo "⚠️  Force stopping $service_name..."
            kill -9 $pid 2>/dev/null
            sleep 1
            if ! lsof -ti:$port > /dev/null 2>&1; then
                echo "✅ $service_name force stopped"
            else
                echo "❌ Failed to stop $service_name"
                return 1
            fi
        fi
    else
        echo "ℹ️  $service_name is not running on port $port"
    fi
    return 0
}

# Stop API server
kill_process_on_port $API_PORT "API server"

# Stop Frontend server
kill_process_on_port $FRONTEND_PORT "Frontend server"

# Also kill any uvicorn or npm dev processes that might be running
echo ""
echo "🧹 Cleaning up any remaining processes..."

# Kill uvicorn processes
uvicorn_pids=$(pgrep -f "uvicorn api.main:app" 2>/dev/null)
if [ ! -z "$uvicorn_pids" ]; then
    echo "   Stopping uvicorn processes..."
    kill $uvicorn_pids 2>/dev/null
fi

# Kill npm dev processes in frontend directory
npm_pids=$(pgrep -f "npm run dev" 2>/dev/null)
if [ ! -z "$npm_pids" ]; then
    echo "   Stopping npm dev processes..."
    kill $npm_pids 2>/dev/null
fi

# Kill vite processes (frontend dev server)
vite_pids=$(pgrep -f "vite" 2>/dev/null)
if [ ! -z "$vite_pids" ]; then
    echo "   Stopping vite processes..."
    kill $vite_pids 2>/dev/null
fi

echo ""
echo "=========================================="
echo "✨ Application stopped"
echo "=========================================="
echo ""
echo "To restart the application, run: ./run_api.sh"
echo ""