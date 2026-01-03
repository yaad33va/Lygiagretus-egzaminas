#!/bin/bash
# run.sh - Automated test runner for Food Processing System

set -e

echo "=========================================="
echo "Food Processing System - Test Runner"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if main executable exists
if [ ! -f "./main" ]; then
    echo -e "${YELLOW}Executable not found. Building...${NC}"
    if [ -f "Makefile" ]; then
        make
    else
        echo -e "${YELLOW}Using direct compilation...${NC}"
        g++ -std=c++14 -O2 -o main main.cpp -lOpenCL -lpthread
    fi
    echo -e "${GREEN}Build complete!${NC}"
    echo ""
fi

# Check if data files exist
if [ ! -f "data1.json" ]; then
    echo -e "${YELLOW}Data files not found. Generating...${NC}"
    python3 generate_data.py
    echo -e "${GREEN}Data generation complete!${NC}"
    echo ""
fi

# Function to run a single test
run_test() {
    local datafile=$1
    local description=$2

    echo "=========================================="
    echo "Test: $datafile"
    echo "Description: $description"
    echo "=========================================="

    # Start C++ program in background
    ./main "$datafile" &
    CPP_PID=$!

    # Wait a bit for C++ to initialize
    sleep 1

    # Start Python program
    python3 worker.py

    # Wait for C++ to finish
    wait $CPP_PID

    echo ""
    echo -e "${GREEN}Test completed for $datafile${NC}"
    echo "Results saved to: results_$datafile"
    echo ""

    # Show summary of results
    if [ -f "results_$datafile" ]; then
        echo "Result summary:"
        grep "Total items processed:" "results_$datafile" || echo "No summary line found"
    fi

    echo ""
    sleep 2
}

# Main menu
echo "Select test to run:"
echo "1) Test data1.json (all items match filters)"
echo "2) Test data2.json (0 items match - fail filter1)"
echo "3) Test data3.json (0 items match - fail filter2)"
echo "4) Test data4.json (partial items match)"
echo "5) Run all tests sequentially"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        run_test "data1.json" "All 300 items match both filters"
        ;;
    2)
        run_test "data2.json" "0 items match (all fail filter1)"
        ;;
    3)
        run_test "data3.json" "0 items match (all fail filter2)"
        ;;
    4)
        run_test "data4.json" "Approximately 100 items match both filters"
        ;;
    5)
        echo -e "${YELLOW}Running all tests...${NC}"
        echo ""
        run_test "data1.json" "All 300 items match both filters"
        run_test "data2.json" "0 items match (all fail filter1)"
        run_test "data3.json" "0 items match (all fail filter2)"
        run_test "data4.json" "Approximately 100 items match both filters"
        echo -e "${GREEN}All tests completed!${NC}"
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Test run complete!"
echo "=========================================="
echo ""
echo "To view results:"
echo "  cat results_data*.json"
echo ""
echo "To run individual tests manually:"
echo "  Terminal 1: ./main data1.json"
echo "  Terminal 2: python3 worker.py"
