#!/bin/bash

# DSPy Agent Demos - Ultra Simple
# Two focused demos showing complete workflows

case "$1" in
    agriculture)
        poetry run python -m agentic_loop.demos.agriculture_demo
        ;;
    ecommerce)
        poetry run python -m agentic_loop.demos.ecommerce_demo
        ;;
    *)
        echo "DSPy Agent Demos"
        echo "=================="
        echo ""
        echo "Usage: ./run_demo.sh [agriculture|ecommerce]"
        echo ""
        echo "Available demos:"
        echo "  agriculture  - Complete farming workflow (weather → planting decision)"
        echo "  ecommerce    - Complete shopping workflow (orders → checkout)"
        echo ""
        echo "Each demo shows a realistic workflow with natural context building"
        echo "and memory management through connected queries."
        exit 1
        ;;
esac