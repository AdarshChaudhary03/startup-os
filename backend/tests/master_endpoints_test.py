"""Master Test Suite for All Backend API Endpoints

This test suite comprehensively tests all backend API endpoints to ensure
they return positive responses and handle requests correctly.
"""

import pytest
import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


class EndpointTestResult:
    """Class to store test results for each endpoint"""
    def __init__(self, endpoint: str, method: str):
        self.endpoint = endpoint
        self.method = method
        self.status_code: Optional[int] = None
        self.response_time: Optional[float] = None
        self.success: bool = False
        self.error: Optional[str] = None
        self.response_data: Optional[Any] = None
        self.test_time: str = datetime.now().isoformat()


class MasterEndpointTester:
    """Master test class for all API endpoints"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)
        self.results: List[EndpointTestResult] = []
        
        # Define all endpoints to test
        self.endpoints = [
            # Health check
            {"method": "GET", "path": "/health", "name": "Health Check"},
            
            # Teams endpoint
            {"method": "GET", "path": "/api/teams", "name": "Get Teams"},
            
            # Agent endpoints
            {"method": "GET", "path": "/api/agents", "name": "List Agents"},
            {"method": "GET", "path": "/api/agents/status", "name": "Agent Status"},
            
            # CEO Chat endpoints
            {"method": "POST", "path": "/api/ceo/chat/start", "name": "CEO Chat Start",
             "payload": {"initial_message": "Test task for endpoint validation"}},
            {"method": "GET", "path": "/api/ceo/chat/sessions", "name": "CEO Chat Sessions"},
            
            # CEO Simplified endpoints
            {"method": "POST", "path": "/api/ceo/simplified/process", "name": "CEO Simplified Process",
             "payload": {"task": "Test task for validation"}},
            
            # CEO Requirements endpoints
            {"method": "POST", "path": "/api/ceo/requirements/gather", "name": "CEO Requirements Gather",
             "payload": {"task": "Test requirements gathering"}},
            
            # Orchestration endpoints
            {"method": "POST", "path": "/api/orchestrate", "name": "Orchestrate",
             "payload": {"directive": "Test orchestration"}},
            {"method": "GET", "path": "/api/orchestration/status", "name": "Orchestration Status"},
            
            # CEO Orchestration endpoints
            {"method": "POST", "path": "/api/ceo/orchestrate", "name": "CEO Orchestrate",
             "payload": {"directive": "Test CEO orchestration"}},
            
            # Agent execution endpoints
            {"method": "POST", "path": "/api/agents/content_writer_v2/execute", "name": "Content Writer Execute",
             "payload": {
                 "task_description": "Write a test article",
                 "content_type": "blog_post",
                 "parameters": {"topic": "Test Topic"}
             }},
            {"method": "POST", "path": "/api/agents/social_media_publisher/execute", "name": "Social Publisher Execute",
             "payload": {
                 "task_description": "Publish test content",
                 "platform": "instagram",
                 "content": {"caption": "Test caption"}
             }},
        ]
    
    async def test_endpoint(self, endpoint_config: Dict[str, Any]) -> EndpointTestResult:
        """Test a single endpoint"""
        result = EndpointTestResult(endpoint_config["path"], endpoint_config["method"])
        
        try:
            start_time = datetime.now()
            
            if endpoint_config["method"] == "GET":
                response = await self.client.get(endpoint_config["path"])
            elif endpoint_config["method"] == "POST":
                payload = endpoint_config.get("payload", {})
                response = await self.client.post(
                    endpoint_config["path"],
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            else:
                raise ValueError(f"Unsupported method: {endpoint_config['method']}")
            
            end_time = datetime.now()
            result.response_time = (end_time - start_time).total_seconds()
            result.status_code = response.status_code
            
            # Check if response is successful (2xx or specific acceptable codes)
            if 200 <= response.status_code < 300:
                result.success = True
                try:
                    result.response_data = response.json()
                except:
                    result.response_data = response.text
            else:
                result.success = False
                result.error = f"HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Error testing {endpoint_config['name']}: {e}")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all endpoints"""
        logger.info("Starting master endpoint test suite...")
        
        # Test all endpoints
        for endpoint in self.endpoints:
            logger.info(f"Testing {endpoint['name']} ({endpoint['method']} {endpoint['path']})...")
            result = await self.test_endpoint(endpoint)
            self.results.append(result)
            
            # Log result
            if result.success:
                logger.info(f"✓ {endpoint['name']}: SUCCESS (Status: {result.status_code}, Time: {result.response_time:.3f}s)")
            else:
                logger.error(f"✗ {endpoint['name']}: FAILED - {result.error}")
        
        # Generate summary
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        
        summary = {
            "test_run_time": datetime.now().isoformat(),
            "total_endpoints_tested": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "results": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time": r.response_time,
                    "error": r.error,
                    "test_time": r.test_time
                }
                for r in self.results
            ]
        }
        
        return summary
    
    async def generate_report(self) -> str:
        """Generate a detailed test report"""
        summary = await self.run_all_tests()
        
        report = f"""
# Backend API Endpoints Test Report

Generated at: {summary['test_run_time']}

## Summary
- Total Endpoints Tested: {summary['total_endpoints_tested']}
- Successful Tests: {summary['successful_tests']}
- Failed Tests: {summary['failed_tests']}
- Success Rate: {summary['success_rate']}

## Detailed Results

### Successful Endpoints
"""
        
        # Add successful endpoints
        successful = [r for r in summary['results'] if r['success']]
        if successful:
            for result in successful:
                report += f"- **{result['method']} {result['endpoint']}**\n"
                report += f"  - Status Code: {result['status_code']}\n"
                report += f"  - Response Time: {result['response_time']:.3f}s\n\n"
        else:
            report += "No successful endpoints.\n\n"
        
        # Add failed endpoints
        report += "### Failed Endpoints\n"
        failed = [r for r in summary['results'] if not r['success']]
        if failed:
            for result in failed:
                report += f"- **{result['method']} {result['endpoint']}**\n"
                report += f"  - Error: {result['error']}\n\n"
        else:
            report += "No failed endpoints. All tests passed!\n\n"
        
        # Add recommendations
        report += "## Recommendations\n"
        if failed:
            report += "1. Investigate and fix the failed endpoints listed above\n"
            report += "2. Check server logs for detailed error information\n"
            report += "3. Ensure all required services and dependencies are running\n"
            report += "4. Verify API authentication and authorization if applicable\n"
        else:
            report += "1. All endpoints are functioning correctly\n"
            report += "2. Consider adding more comprehensive test cases\n"
            report += "3. Monitor endpoint performance for optimization opportunities\n"
        
        return report
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def main():
    """Main function to run the master test suite"""
    tester = MasterEndpointTester()
    
    try:
        # Generate and print the report
        report = await tester.generate_report()
        print(report)
        
        # Save report to file
        report_filename = f"endpoint_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_filename}")
        
    finally:
        await tester.close()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())
