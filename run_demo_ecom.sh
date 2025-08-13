#!/bin/bash

# Complex E-commerce Demo Scenarios for DSPy Agentic Loop
# These test cases showcase sophisticated multi-step reasoning and tool orchestration

show_help() {
    echo "🛍️ DSPy Agentic Loop - E-commerce Demo Suite"
    echo ""
    echo "Usage: ./run_demo_ecom.sh [TEST_NUMBER] [OPTIONS]"
    echo ""
    echo "Test Scenarios:"
    echo "  1  - Multi-step purchase with budget constraints"
    echo "  2  - Comparative shopping with price optimization"
    echo "  3  - Order tracking and conditional return processing"
    echo "  4  - Cart optimization with inventory awareness"
    echo "  5  - Complex return with refund verification"
    echo "  6  - Multi-user gift shopping scenario"
    echo "  7  - Abandoned cart recovery with alternatives"
    echo "  8  - Order history analysis with reorder"
    echo "  9  - Bundle shopping with compatibility check"
    echo "  10 - Customer service escalation flow"
    echo ""
    echo "Options:"
    echo "  --verbose, -v    Show agent thoughts and tool results"
    echo "  --debug, -d      Enable full DSPy debug output"
    echo "  --help, -h       Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_demo_ecom.sh           # Run all test cases"
    echo "  ./run_demo_ecom.sh 3         # Run test case 3 only"
    echo "  ./run_demo_ecom.sh 5 -v      # Run test 5 with verbose output"
    echo ""
    exit 0
}

# Array of complex test queries
declare -a QUERIES=(
    # Test 1: Multi-step purchase with budget constraints
    "I have a budget of \$1500. I need to buy a laptop for work and a wireless mouse. Find the best laptop under my budget, add it to my cart with a compatible mouse, and then checkout to 789 Tech Ave."
    
    # Test 2: Comparative shopping with price optimization
    "Compare gaming keyboards under \$150 and wireless headphones under \$100. Add the highest-rated item from each category to my cart, but only if the total stays under \$200."
    
    # Test 3: Order tracking and conditional return
    "For user demo_user, check the status of their most recent order. If it's been delivered and contains any electronics over \$500, initiate a return for the most expensive item citing 'changed mind'."
    
    # Test 4: Cart optimization with inventory awareness
    "I want to buy 3 wireless mice and 2 mechanical keyboards. Add them to my cart but if any item has less than 5 units in stock, reduce my quantity to leave at least 2 for other customers."
    
    # Test 5: Complex return with refund verification
    "For user demo_user, list all their delivered orders from the past month. For any order over \$300, check if it contains laptops or monitors, and if so, process a return for quality issues and tell me the expected refund amount."
    
    # Test 6: Multi-user gift shopping scenario
    "I need to buy gifts for 3 different people. Find a laptop under \$1000 for person A, gaming accessories under \$200 for person B, and the best-rated wireless earbuds for person C. Add all to cart and calculate the total."
    
    # Test 7: Abandoned cart recovery with alternatives
    "Check what's currently in my cart. If the total is over \$500 and includes any out-of-stock items, remove them and suggest similar alternatives that are in stock."
    
    # Test 8: Order history analysis with reorder
    "For user demo_user, review their last 5 orders and identify the most frequently purchased category. Then search for new products in that category and add the top-rated one to their cart if it's different from what they've bought before."
    
    # Test 9: Bundle shopping with compatibility check
    "I'm setting up a home office. Find a laptop, monitor, keyboard, and mouse that are all compatible and stay within a \$2000 budget. Prioritize items that are frequently bought together."
    
    # Test 10: Customer service escalation flow
    "I received order ORD-2019 but one item was damaged. First check the order details, then process a return for the damaged item with reason 'arrived damaged', and add a replacement to my cart for immediate reorder."
)

# Process command line arguments
VERBOSE_MODE=""
DEBUG_MODE=""
TEST_NUMBER=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --debug|-d)
            echo "🐛 Debug mode enabled"
            DEBUG_MODE="true"
            export DSPY_DEBUG=true
            shift
            ;;
        --verbose|-v)
            echo "📢 Verbose mode enabled"
            VERBOSE_MODE="true"
            export DEMO_VERBOSE=true
            shift
            ;;
        [1-9]|10)
            TEST_NUMBER=$1
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to run a single test
run_test() {
    local test_num=$1
    local query="${QUERIES[$test_num-1]}"
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "🧪 Test Case #$test_num"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "📝 Query: $query"
    echo ""
    echo "🤖 Running agentic loop..."
    echo "───────────────────────────────────────────────────────────────"
    
    # Run the demo with the query
    echo "$query" | poetry run python run_ecom_query.py
    
    echo "───────────────────────────────────────────────────────────────"
    echo "✅ Test Case #$test_num completed"
    echo ""
}

# Function to initialize the database
init_database() {
    echo "🔧 Initializing database with demo data..."
    poetry run python -c "
from tools.ecommerce.cart_inventory_manager import CartInventoryManager
manager = CartInventoryManager()
manager.reset_database()
print('✅ Database initialized successfully')
"
}

# Main execution
echo "🛍️ E-commerce Demo Suite for DSPy Agentic Loop"
echo "══════════════════════════════════════════════════════════════"

# Initialize database before running tests
init_database

if [ -z "$TEST_NUMBER" ]; then
    # Run all tests
    echo ""
    echo "🚀 Running all 10 test cases..."
    echo ""
    
    for i in {1..10}; do
        run_test $i
        
        # Add a pause between tests except for the last one
        if [ $i -lt 10 ]; then
            echo "⏸️  Pausing before next test..."
            sleep 2
        fi
    done
    
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "🎉 All test cases completed!"
    echo ""
else
    # Run specific test
    if [ "$TEST_NUMBER" -ge 1 ] && [ "$TEST_NUMBER" -le 10 ]; then
        run_test $TEST_NUMBER
    else
        echo "❌ Invalid test number: $TEST_NUMBER"
        echo "Please choose a number between 1 and 10"
        exit 1
    fi
fi

echo "📊 Demo session complete"