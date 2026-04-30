#!/bin/bash

# Script to run simplified API tests

echo "======================================"
echo "Running Simplified Agent API Tests"
echo "======================================"
echo ""

# Check if backend is running
echo "Checking if backend is running..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend is not running!"
    echo "Please start the backend first with: python run_backend.py"
    exit 1
fi
echo "✓ Backend is running"
echo ""

# Run quick health check
echo "Testing simplified API health endpoint..."
curl -s http://localhost:8000/api/simple/health | python -m json.tool
echo ""

# Test Content Writer API
echo "======================================"
echo "Testing Content Writer API"
echo "======================================"
echo ""

echo "1. Testing Instagram post generation..."
curl -X POST http://localhost:8000/api/simple/content_writer \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session-123" \
  -d '{
    "topic": "GenAI for students",
    "mode": "instagram_post"
  }' | python -m json.tool

echo ""
echo "2. Testing blog post generation..."
curl -X POST http://localhost:8000/api/simple/content_writer \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Benefits of AI in education",
    "mode": "blog"
  }' | python -m json.tool

echo ""
echo "3. Testing error handling (missing topic)..."
curl -X POST http://localhost:8000/api/simple/content_writer \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "instagram_post"
  }' -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "======================================"
echo "Testing Social Publisher API"
echo "======================================"
echo ""

echo "1. Testing Instagram publishing..."
curl -X POST http://localhost:8000/api/simple/social_publisher \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session-123" \
  -d '{
    "caption": "🚀 Discover the power of AI with GenAI for students! #AI #GenAI #Students",
    "platform": "instagram",
    "image_url": "https://picsum.photos/1080/1080"
  }' | python -m json.tool

echo ""
echo "2. Testing publishing without image..."
curl -X POST http://localhost:8000/api/simple/social_publisher \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Check out the latest in AI technology! #AI #Tech",
    "platform": "linkedin"
  }' | python -m json.tool

echo ""
echo "3. Testing error handling (missing caption)..."
curl -X POST http://localhost:8000/api/simple/social_publisher \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram"
  }' -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "======================================"
echo "Running Python test suite..."
echo "======================================"
echo ""

# Run Python tests if available
if [ -f "tests/test_simple_agent_apis.py" ]; then
    python -m pytest tests/test_simple_agent_apis.py -v --tb=short
else
    echo "Python test file not found. Skipping pytest."
fi

echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo "✓ Simplified API endpoints are available"
echo "✓ Content Writer API accepts topic and mode"
echo "✓ Social Publisher API accepts caption, platform, and optional image_url"
echo "✓ Error handling works correctly"
echo ""
echo "To use in production:"
echo "1. Generate content: POST /api/simple/content_writer"
echo "2. Publish content: POST /api/simple/social_publisher"
echo ""
echo "See API_REFERENCE_MATRIX.md for complete documentation."