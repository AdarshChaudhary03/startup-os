#!/bin/bash

# Instagram API Test Script
# This script sets up environment variables and runs the Instagram API test

echo "🧪 Instagram API Test Runner"
echo "============================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# Install required packages if not available
echo "📦 Installing required packages..."
pip install requests

# Set environment variables (replace with your actual values)
echo "🔧 Setting up environment variables..."
export INSTAGRAM_ACCESS_TOKEN="EAAaaZBVbXxHkBRRmKJPRSkGS2RMDnRCoVqA0f3qwjZACnZAfD8ikv2jFWZAG4MSY4lbdqkPPZBvJce1Y5ctfL8olenkkNaCgUDGWoaDY6NtQwxoOwoiwDvqntCBRVtIrIlvDJ5FBA7st17HZCG3TQIWVMyIEmRKuiyxmfPCVRtGfNL8HdUh3gTM5Q8ZAmK3mwZDZD"
export INSTAGRAM_USER_ID="17841439653964722"

echo "🚀 Running Instagram API test..."
python3 test_instagram_curl.py

echo "\n✅ Test completed!"
echo "\n📋 Manual cURL Commands for Testing:"
echo "====================================="
echo ""
echo "1. Test Access Token:"
echo "curl -X GET 'https://graph.facebook.com/v18.0/me?access_token=$INSTAGRAM_ACCESS_TOKEN'"
echo ""
echo "2. Test Instagram Account:"
echo "curl -X GET 'https://graph.facebook.com/v18.0/$INSTAGRAM_USER_ID?fields=account_type,username,name&access_token=$INSTAGRAM_ACCESS_TOKEN'"
echo ""
echo "3. Create Media Container:"
echo "curl -X POST 'https://graph.facebook.com/v18.0/$INSTAGRAM_USER_ID/media' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"image_url\": \"https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg\","
echo "    \"caption\": \"Test post from cURL\","
echo "    \"access_token\": \"'$INSTAGRAM_ACCESS_TOKEN'\""
echo "  }'"
echo ""
echo "4. Publish Media (use container ID from step 3):"
echo "curl -X POST 'https://graph.facebook.com/v18.0/$INSTAGRAM_USER_ID/media_publish' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"creation_id\": \"CONTAINER_ID_FROM_STEP_3\","
echo "    \"access_token\": \"'$INSTAGRAM_ACCESS_TOKEN'\""
echo "  }'"
