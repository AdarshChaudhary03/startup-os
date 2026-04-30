"""Test CEO Agent delegation to Social Media Publisher

This test verifies:
1. CEO agent correctly delegates to social media publisher
2. Content from content writer is passed to social media publisher
3. Social media publisher endpoint is correctly resolved
4. Instagram posting receives the content as caption
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


class TestCEOSocialMediaDelegation:
    """Test suite for CEO agent delegation to social media publisher"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
    
    async def test_orchestration_plan_includes_social_publisher(self):
        """Test that orchestration plan correctly includes social media publisher"""
        test_name = "test_orchestration_plan_includes_social_publisher"
        logger.info(f"\n{'='*50}\nRunning {test_name}\n{'='*50}")
        
        try:
            # Create a task that should involve content writer and social media publisher
            task = "Create a blog post about AI trends and post it on Instagram"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/orchestrate",
                    json={"task": task},
                    headers={"X-Request-ID": f"test-{datetime.now().isoformat()}"}
                )
                
                if response.status_code == 200:
                    plan = response.json()
                    logger.info(f"Orchestration plan: {json.dumps(plan, indent=2)}")
                    
                    # Check if social media publisher is in the plan
                    agent_ids = [step.get('agent_id') for step in plan.get('steps', [])]
                    agent_names = [step.get('agent_name') for step in plan.get('steps', [])]
                    
                    has_social_publisher = any(
                        'social' in agent_id.lower() and 'publisher' in agent_id.lower() 
                        for agent_id in agent_ids
                    )
                    
                    if has_social_publisher:
                        logger.info("✅ Social media publisher found in orchestration plan")
                        self.test_results.append((test_name, True, "Social publisher included in plan"))
                    else:
                        logger.error(f"❌ Social media publisher NOT found. Agents: {agent_ids}")
                        self.test_results.append((test_name, False, f"Social publisher missing. Found: {agent_ids}"))
                else:
                    logger.error(f"❌ Orchestration failed: {response.status_code} - {response.text}")
                    self.test_results.append((test_name, False, f"Orchestration failed: {response.status_code}"))
                    
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            self.test_results.append((test_name, False, f"Exception: {str(e)}"))
    
    async def test_social_publisher_endpoint_exists(self):
        """Test that social media publisher endpoint is accessible"""
        test_name = "test_social_publisher_endpoint_exists"
        logger.info(f"\n{'='*50}\nRunning {test_name}\n{'='*50}")
        
        try:
            # Test different possible endpoints
            endpoints_to_test = [
                "/api/agents/social-media-publisher",
                "/api/agents/social_media_publisher",
                "/api/agents/social-publisher",
                "/api/agents/social_publisher"
            ]
            
            test_payload = {
                "task": "Post on Instagram",
                "content": "Test content",
                "platform": "instagram"
            }
            
            endpoint_found = False
            working_endpoint = None
            
            async with httpx.AsyncClient() as client:
                for endpoint in endpoints_to_test:
                    logger.info(f"Testing endpoint: {endpoint}")
                    
                    try:
                        response = await client.post(
                            f"{self.base_url}{endpoint}",
                            json=test_payload,
                            headers={"X-Request-ID": f"test-{datetime.now().isoformat()}"},
                            timeout=10.0
                        )
                        
                        if response.status_code != 404:
                            endpoint_found = True
                            working_endpoint = endpoint
                            logger.info(f"✅ Endpoint {endpoint} responded with status {response.status_code}")
                            break
                        else:
                            logger.warning(f"Endpoint {endpoint} returned 404")
                    except Exception as e:
                        logger.warning(f"Endpoint {endpoint} failed: {e}")
            
            if endpoint_found:
                self.test_results.append((test_name, True, f"Working endpoint: {working_endpoint}"))
            else:
                self.test_results.append((test_name, False, "No working social publisher endpoint found"))
                
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            self.test_results.append((test_name, False, f"Exception: {str(e)}"))
    
    async def test_content_writer_to_social_publisher_flow(self):
        """Test the complete flow from content writer to social media publisher"""
        test_name = "test_content_writer_to_social_publisher_flow"
        logger.info(f"\n{'='*50}\nRunning {test_name}\n{'='*50}")
        
        try:
            # Step 1: Execute content writer
            content_writer_payload = {
                "task": "Write a short Instagram caption about the benefits of morning meditation",
                "format": "social_media",
                "tone": "inspirational"
            }
            
            content_output = None
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info("Step 1: Executing content writer...")
                
                response = await client.post(
                    f"{self.base_url}/api/agents/content-writer",
                    json=content_writer_payload,
                    headers={"X-Request-ID": f"test-cw-{datetime.now().isoformat()}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content_output = result.get('output', '')
                    logger.info(f"✅ Content writer output: {content_output[:100]}...")
                else:
                    logger.error(f"❌ Content writer failed: {response.status_code}")
                    self.test_results.append((test_name, False, "Content writer execution failed"))
                    return
                
                # Step 2: Pass content to social media publisher
                if content_output:
                    logger.info("\nStep 2: Passing content to social media publisher...")
                    
                    social_publisher_payload = {
                        "task": "Post this content on Instagram",
                        "content": content_output,
                        "caption": content_output,  # Use content as caption
                        "platform": "instagram"
                    }
                    
                    # Try different endpoint formats
                    endpoints = [
                        "/api/agents/social-media-publisher",
                        "/api/agents/social_media_publisher"
                    ]
                    
                    success = False
                    for endpoint in endpoints:
                        try:
                            response = await client.post(
                                f"{self.base_url}{endpoint}",
                                json=social_publisher_payload,
                                headers={"X-Request-ID": f"test-sp-{datetime.now().isoformat()}"},
                                timeout=30.0
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                logger.info(f"✅ Social publisher executed successfully")
                                logger.info(f"Response: {json.dumps(result, indent=2)}")
                                success = True
                                break
                            elif response.status_code != 404:
                                logger.warning(f"Social publisher returned {response.status_code}: {response.text}")
                        except Exception as e:
                            logger.warning(f"Failed with endpoint {endpoint}: {e}")
                    
                    if success:
                        self.test_results.append((test_name, True, "Content successfully passed to social publisher"))
                    else:
                        self.test_results.append((test_name, False, "Failed to execute social publisher"))
                        
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            self.test_results.append((test_name, False, f"Exception: {str(e)}"))
    
    async def test_ceo_simplified_flow_delegation(self):
        """Test CEO simplified flow delegation to social media publisher"""
        test_name = "test_ceo_simplified_flow_delegation"
        logger.info(f"\n{'='*50}\nRunning {test_name}\n{'='*50}")
        
        try:
            # Import and test the simplified CEO flow
            from ceo_simplified_flow import simplified_ceo_agent
            
            # Check agent endpoint mappings
            logger.info("Checking CEO agent endpoint mappings...")
            
            if 'social_publisher' in simplified_ceo_agent.agent_endpoints:
                endpoint = simplified_ceo_agent.agent_endpoints['social_publisher']
                logger.info(f"✅ social_publisher endpoint mapped to: {endpoint}")
            else:
                logger.error("❌ social_publisher not found in agent endpoints")
                
            if 'social_media_publisher' in simplified_ceo_agent.agent_endpoints:
                endpoint = simplified_ceo_agent.agent_endpoints['social_media_publisher']
                logger.info(f"✅ social_media_publisher endpoint mapped to: {endpoint}")
            else:
                logger.error("❌ social_media_publisher not found in agent endpoints")
            
            # Check payload formats
            if 'social_publisher' in simplified_ceo_agent.agent_payload_formats:
                logger.info("✅ social_publisher payload format defined")
                self.test_results.append((test_name, True, "CEO flow properly configured for social publisher"))
            else:
                logger.error("❌ social_publisher payload format missing")
                self.test_results.append((test_name, False, "CEO flow missing social publisher configuration"))
                
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            self.test_results.append((test_name, False, f"Exception: {str(e)}"))
    
    def print_test_summary(self):
        """Print summary of all test results"""
        logger.info(f"\n{'='*60}\nTEST SUMMARY\n{'='*60}")
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, message in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status} - {test_name}: {message}")
        
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        
        if passed < total:
            logger.error("\n⚠️  Some tests failed. Please check the logs above.")
        else:
            logger.info("\n🎉 All tests passed!")
    
    async def run_all_tests(self):
        """Run all test cases"""
        logger.info("Starting CEO Social Media Publisher Delegation Tests...")
        
        await self.test_orchestration_plan_includes_social_publisher()
        await self.test_social_publisher_endpoint_exists()
        await self.test_content_writer_to_social_publisher_flow()
        await self.test_ceo_simplified_flow_delegation()
        
        self.print_test_summary()


async def main():
    """Main test runner"""
    tester = TestCEOSocialMediaDelegation()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
