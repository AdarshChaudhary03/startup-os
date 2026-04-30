#!/usr/bin/env python3
"""
Test script to debug CEO chat orchestration flow

This script simulates the CEO chat flow to identify why mode and agents are undefined
and why the system reports success without actually executing tasks.
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = "http://localhost:8000"


async def test_ceo_chat_flow():
    """Test the complete CEO chat flow from start to orchestration"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Start chat session
        logger.info("=== Step 1: Starting CEO chat session ===")
        start_response = await client.post(
            f"{BASE_URL}/api/ceo/chat/start",
            json={
                "initial_message": "Create a blog post about AI trends in 2024"
            }
        )
        
        if start_response.status_code != 200:
            logger.error(f"Failed to start chat: {start_response.status_code} - {start_response.text}")
            return
        
        start_data = start_response.json()
        conversation_id = start_data["conversation_id"]
        logger.info(f"Chat started with conversation_id: {conversation_id}")
        logger.info(f"Initial response: {json.dumps(start_data, indent=2)}")
        
        # Step 2: Send a few messages to answer questions
        logger.info("\n=== Step 2: Answering CEO questions ===")
        
        # Simulate user responses
        messages = [
            "The purpose is to educate readers about the latest AI trends and technologies that will shape 2024.",
            "The target audience is tech professionals, business leaders, and AI enthusiasts.",
            "It should be around 1000 words, include current trends, practical examples, and future predictions."
        ]
        
        for i, message in enumerate(messages):
            logger.info(f"\nSending message {i+1}: {message[:50]}...")
            
            msg_response = await client.post(
                f"{BASE_URL}/api/ceo/chat/message",
                json={
                    "conversation_id": conversation_id,
                    "message": message
                }
            )
            
            if msg_response.status_code != 200:
                logger.error(f"Failed to send message: {msg_response.status_code} - {msg_response.text}")
                continue
            
            msg_data = msg_response.json()
            logger.info(f"CEO response: {msg_data.get('message', 'No message')}")
            logger.info(f"Current state: {msg_data.get('state', 'Unknown')}")
            
            # Check if requirements are complete
            if msg_data.get("state") == "requirements_complete":
                logger.info("Requirements gathering complete!")
                break
            
            # Small delay between messages
            await asyncio.sleep(1)
        
        # Step 3: Finalize requirements
        logger.info("\n=== Step 3: Finalizing requirements ===")
        
        finalize_response = await client.post(
            f"{BASE_URL}/api/ceo/chat/{conversation_id}/finalize"
        )
        
        if finalize_response.status_code != 200:
            logger.error(f"Failed to finalize: {finalize_response.status_code} - {finalize_response.text}")
            return
        
        finalize_data = finalize_response.json()
        logger.info(f"\nFinalization response:")
        logger.info(json.dumps(finalize_data, indent=2))
        
        # Analyze the response
        logger.info("\n=== Analysis of Response ===")
        logger.info(f"Has requirements: {'requirements' in finalize_data}")
        logger.info(f"Has plan: {'plan' in finalize_data}")
        logger.info(f"Has agent_plan: {'agent_plan' in finalize_data}")
        logger.info(f"Has orchestration_result: {'orchestration_result' in finalize_data}")
        
        if 'plan' in finalize_data:
            plan = finalize_data['plan']
            logger.info(f"\nPlan details:")
            logger.info(f"  - Mode: {plan.get('mode', 'UNDEFINED')}")
            logger.info(f"  - Ready for execution: {plan.get('ready_for_execution', False)}")
        
        if 'orchestration_result' in finalize_data:
            orch_result = finalize_data['orchestration_result']
            if orch_result:
                logger.info(f"\nOrchestration result:")
                logger.info(f"  - Type: {type(orch_result)}")
                if isinstance(orch_result, dict):
                    logger.info(f"  - Mode: {orch_result.get('mode', 'UNDEFINED')}")
                    logger.info(f"  - Steps: {len(orch_result.get('steps', []))}")
                    logger.info(f"  - Rationale: {orch_result.get('rationale', 'UNDEFINED')}")
            else:
                logger.warning("Orchestration result is None or empty")
        else:
            logger.warning("No orchestration_result in response")
        
        # Step 4: Check backend logs
        logger.info("\n=== Next Steps ===")
        logger.info("1. Check backend logs for [CEO_CHAT_DEBUG] entries")
        logger.info("2. Check browser console for [CEO_DEBUG] entries")
        logger.info("3. Verify orchestration endpoint is being called")
        logger.info("4. Check if agent plan creation is successful")


async def test_direct_orchestration():
    """Test calling orchestration endpoint directly"""
    
    logger.info("\n=== Testing Direct Orchestration ===")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/orchestrate",
            json={
                "task": "Create a blog post about AI trends in 2024 for tech professionals"
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Orchestration failed: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        logger.info(f"\nDirect orchestration response:")
        logger.info(json.dumps(data, indent=2))
        
        logger.info(f"\nOrchestration details:")
        logger.info(f"  - Mode: {data.get('mode', 'UNDEFINED')}")
        logger.info(f"  - Rationale: {data.get('rationale', 'UNDEFINED')}")
        logger.info(f"  - Steps: {len(data.get('steps', []))}")
        logger.info(f"  - Total steps: {data.get('total_steps', 0)}")


async def main():
    """Run all tests"""
    
    logger.info("Starting CEO Chat Debug Tests")
    logger.info("=" * 50)
    
    # Test CEO chat flow
    await test_ceo_chat_flow()
    
    # Test direct orchestration for comparison
    await test_direct_orchestration()
    
    logger.info("\n" + "=" * 50)
    logger.info("Tests completed. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
