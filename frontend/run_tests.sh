#!/bin/bash

# Frontend State Management Tests Runner

echo "========================================"
echo "Running Frontend State Management Tests"
echo "========================================"

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Run the state management tests
echo ""
echo "Running AgentStore tests..."
npm test -- src/store/__tests__/agentStore.test.js --coverage

echo ""
echo "Running AgentOutputManager tests..."
npm test -- src/services/__tests__/agentOutputManager.test.js --coverage

echo ""
echo "Running all state management related tests..."
npm test -- --testPathPattern="(agentStore|agentOutputManager)" --coverage

echo ""
echo "========================================"
echo "Test execution completed!"
echo "========================================"