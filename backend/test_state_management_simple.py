"""Simple test script for state management content passing"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_state_manager import state_manager
    print("✓ Successfully imported state_manager")
except Exception as e:
    print(f"✗ Failed to import state_manager: {e}")
    exit(1)

# Test 1: Save and retrieve content
print("\nTest 1: Save and retrieve content")
test_session_id = "test_session_123"
test_content = "🚀 Upskill with GenAI 🤖 Learn the latest in AI #AIforIT #GenAI #ITprofessionals"

try:
    # Save content as Content Writer would
    state_id = state_manager.save_agent_output(
        session_id=test_session_id,
        agent_id="content_writer",
        output=test_content,
        metadata={"test": True}
    )
    print(f"✓ Saved content with state_id: {state_id}")
    
    # Retrieve content as Social Media Publisher would
    retrieved_content = state_manager.get_agent_output(test_session_id, "content_writer")
    
    if retrieved_content == test_content:
        print(f"✓ Retrieved correct content: {retrieved_content[:50]}...")
    else:
        print(f"✗ Retrieved wrong content: {retrieved_content}")
        
except Exception as e:
    print(f"✗ Test 1 failed: {e}")

# Test 2: Get previous agent output
print("\nTest 2: Get previous agent output")
try:
    # Save another agent's output
    state_manager.save_agent_output(
        session_id=test_session_id,
        agent_id="qa_tester",
        output="Content validated",
        metadata={"test": True}
    )
    
    # Get previous output
    previous_output = state_manager.get_previous_agent_output(
        session_id=test_session_id,
        current_agent_id="social_publisher",
        previous_agent_id="content_writer"
    )
    
    if previous_output == test_content:
        print(f"✓ Got correct previous output from content_writer")
    else:
        print(f"✗ Got wrong previous output: {previous_output}")
        
except Exception as e:
    print(f"✗ Test 2 failed: {e}")

# Test 3: Session summary
print("\nTest 3: Session summary")
try:
    summary = state_manager.get_session_summary(test_session_id)
    print(f"✓ Session summary: {summary['total_agents']} agents, {summary['agents']}")
except Exception as e:
    print(f"✗ Test 3 failed: {e}")

# Cleanup
print("\nCleaning up test data...")
try:
    state_manager.clear_session_state(test_session_id)
    print("✓ Cleanup successful")
except Exception as e:
    print(f"✗ Cleanup failed: {e}")

print("\n=== State Management Tests Complete ===")
