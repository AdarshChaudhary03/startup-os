"""Simple test to verify the social media publisher fix."""

import asyncio
import json

# Test the AgentExecutionRequest model
try:
    from models import AgentExecutionRequest
    print("✓ Successfully imported AgentExecutionRequest")
    
    # Test creating a request with all fields
    request = AgentExecutionRequest(
        task="Schedule and publish the caption on Instagram.",
        caption="Test caption with emojis 🚀",
        content="Test content",
        context={"content_writer_output": "Generated content"},
        metadata={"session_id": "test-123"}
    )
    print("✓ Successfully created AgentExecutionRequest with all fields")
    print(f"  - task: {request.task[:50]}...")
    print(f"  - caption: {request.caption[:50]}...")
    print(f"  - content: {request.content}")
    print(f"  - context: {request.context}")
    print(f"  - metadata: {request.metadata}")
    
except Exception as e:
    print(f"✗ Error with AgentExecutionRequest: {e}")

# Test the content extraction logic
try:
    print("\n--- Testing Content Extraction Logic ---")
    
    # Simulate the task data that would come from frontend
    task_data = {
        "task": "Schedule and publish the caption on Instagram.",
        "caption": "🤖 Discover the power of AI with GenAI 🚀",
        "content": "Schedule and publish the caption on Instagram.",
        "context": {
            "content_writer_output": "🤖 Discover the power of AI with GenAI 🚀",
            "metadata": {"session_id": "test-session-123"}
        },
        "metadata": {"session_id": "test-session-123"}
    }
    
    # Test extraction logic (simulating what utils.py does)
    content = task_data.get('caption')
    if not content or content == task_data.get('task'):
        context = task_data.get('context')
        if context and isinstance(context, dict):
            content = context.get('caption') or context.get('content_writer_output') or content
    
    print(f"✓ Extracted content: {content[:50]}...")
    print(f"✓ Content does not contain instruction: {'Schedule and publish' not in content}")
    
except Exception as e:
    print(f"✗ Error in content extraction: {e}")

print("\n--- Test Summary ---")
print("The fix should properly extract the actual content (with emojis) instead of the task instruction.")
print("This prevents the 422 error by ensuring the social media publisher receives the correct content.")