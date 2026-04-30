#!/usr/bin/env python3
"""
Content Writer v2 - Comprehensive Test Suite

This script tests all aspects of the Content Writer v2 system including:
- Main agent initialization
- Sub-agent classification
- Content generation for different types
- Platform-specific optimization
- Error handling
- Performance metrics
"""

import asyncio
import time
import json
import os
from typing import Dict, Any, List

# Test imports
try:
    from content_writer_v2.main_agent import ContentWriterMainAgent
    from content_writer_v2.config import DEFAULT_CONFIG, ContentCategory, SocialPlatform
    from content_writer_v2.factory import ContentAgentFactory
    from content_writer_v2.sub_agents import (
        SocialMediaAgent, BlogAgent, ScriptAgent, 
        MarketingCopyAgent, TechnicalWritingAgent
    )
    print("✅ All Content Writer v2 imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)


class ContentWriterV2Tester:
    """Comprehensive test suite for Content Writer v2."""
    
    def __init__(self):
        self.main_agent = None
        self.test_results = []
        self.performance_metrics = []
    
    async def setup(self):
        """Initialize the main agent for testing."""
        print("\n🔧 Setting up Content Writer v2 Main Agent...")
        
        try:
            self.main_agent = ContentWriterMainAgent(DEFAULT_CONFIG)
            await self.main_agent.initialize()
            print("✅ Main agent initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Main agent initialization failed: {e}")
            return False
    
    async def test_environment(self):
        """Test environment configuration."""
        print("\n🌍 Testing Environment Configuration...")
        
        # Check API key
        groq_key = os.getenv('GROQ_API_KEY')
        if not groq_key:
            print("❌ GROQ_API_KEY not set")
            return False
        
        if not groq_key.startswith('gsk_'):
            print("❌ Invalid GROQ_API_KEY format")
            return False
        
        print("✅ GROQ_API_KEY configured correctly")
        
        # Check configuration
        config = DEFAULT_CONFIG
        print(f"✅ Provider: {config.ai_provider.provider}")
        print(f"✅ Model: {config.ai_provider.model}")
        print(f"✅ Temperature: {config.ai_provider.temperature}")
        
        return True
    
    async def test_task_classification(self):
        """Test automatic task classification."""
        print("\n🧠 Testing Task Classification...")
        
        test_cases = [
            ("Write an Instagram caption for a sunny day", ContentCategory.SOCIAL_MEDIA),
            ("Create a blog post about AI in healthcare", ContentCategory.BLOG),
            ("Write a 30-second reel script about fitness", ContentCategory.SCRIPT),
            ("Create ad copy for a new mobile app", ContentCategory.MARKETING),
            ("Write API documentation for user authentication", ContentCategory.TECHNICAL)
        ]
        
        for task, expected_category in test_cases:
            classified_category = ContentAgentFactory._classify_task(task)
            
            if classified_category == expected_category:
                print(f"✅ '{task[:30]}...' → {classified_category.value}")
            else:
                print(f"❌ '{task[:30]}...' → Expected: {expected_category.value}, Got: {classified_category.value}")
                return False
        
        return True
    
    async def test_social_media_agent(self):
        """Test Social Media Agent functionality."""
        print("\n📱 Testing Social Media Agent...")
        
        try:
            social_agent = SocialMediaAgent(DEFAULT_CONFIG)
            await social_agent.initialize()
            
            # Test Instagram caption
            result = await social_agent.generate_content(
                task="sunny day in Delhi",
                request_id="test_social_instagram",
                platform=SocialPlatform.INSTAGRAM,
                include_hashtags=True,
                include_emojis=True
            )
            
            content = result["content"]
            hashtags = result.get("hashtags", [])
            metadata = result.get("metadata", {})
            
            # Validate Instagram-specific requirements
            if len(content) > 2200:
                print(f"❌ Instagram content too long: {len(content)} chars")
                return False
            
            if len(hashtags) == 0:
                print("❌ No hashtags generated for Instagram")
                return False
            
            if not any(char for char in content if ord(char) > 127):  # Check for emojis
                print("❌ No emojis found in Instagram content")
                return False
            
            print(f"✅ Instagram caption generated: {len(content)} chars, {len(hashtags)} hashtags")
            print(f"   Preview: {content[:100]}...")
            print(f"   Hashtags: {hashtags[:5]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Social Media Agent test failed: {e}")
            return False
    
    async def test_blog_agent(self):
        """Test Blog Agent functionality."""
        print("\n📝 Testing Blog Agent...")
        
        try:
            blog_agent = BlogAgent(DEFAULT_CONFIG)
            await blog_agent.initialize()
            
            # Test blog post generation
            result = await blog_agent.generate_content(
                task="Benefits of AI in healthcare",
                request_id="test_blog",
                word_count=500,
                seo_keywords=["AI healthcare", "medical technology"],
                include_outline=True
            )
            
            content = result["content"]
            analysis = result.get("content_analysis", {})
            outline = result.get("outline")
            
            # Validate blog-specific requirements
            word_count = analysis.get("word_count", 0)
            if word_count < 300:
                print(f"❌ Blog post too short: {word_count} words")
                return False
            
            if not content.startswith("#") and "#" not in content:
                print("❌ No proper heading structure found")
                return False
            
            print(f"✅ Blog post generated: {word_count} words")
            print(f"   Readability score: {analysis.get('readability_score', 'N/A')}")
            print(f"   Structure score: {analysis.get('structure_score', 'N/A')}")
            if outline:
                print(f"   Outline generated: {len(outline)} chars")
            
            return True
            
        except Exception as e:
            print(f"❌ Blog Agent test failed: {e}")
            return False
    
    async def test_script_agent(self):
        """Test Script Agent functionality."""
        print("\n🎬 Testing Script Agent...")
        
        try:
            script_agent = ScriptAgent(DEFAULT_CONFIG)
            await script_agent.initialize()
            
            # Test reel script generation
            result = await script_agent.generate_content(
                task="morning routine tips",
                request_id="test_script",
                script_type="reel",
                duration_seconds=30,
                include_timing=True,
                include_visual_cues=True
            )
            
            content = result["content"]
            analysis = result.get("script_analysis", {})
            
            # Validate script-specific requirements
            estimated_duration = analysis.get("estimated_duration_seconds", 0)
            if abs(estimated_duration - 30) > 10:  # Allow 10-second variance
                print(f"❌ Script duration off target: {estimated_duration}s vs 30s")
                return False
            
            if "[0:" not in content:
                print("❌ No timing markers found in script")
                return False
            
            if "[Visual:" not in content:
                print("❌ No visual cues found in script")
                return False
            
            print(f"✅ Reel script generated: {estimated_duration}s duration")
            print(f"   Word count: {analysis.get('word_count', 'N/A')}")
            print(f"   Scene count: {analysis.get('scene_count', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Script Agent test failed: {e}")
            return False
    
    async def test_main_agent_integration(self):
        """Test Main Agent with automatic sub-agent selection."""
        print("\n🎯 Testing Main Agent Integration...")
        
        test_cases = [
            {
                "task": "Write an Instagram caption for a coffee shop",
                "expected_category": "social_media",
                "expected_agent": "SocialMediaAgent"
            },
            {
                "task": "Create a blog post about sustainable living",
                "expected_category": "blog",
                "expected_agent": "BlogAgent"
            },
            {
                "task": "Write a script for a TikTok video about cooking",
                "expected_category": "script",
                "expected_agent": "ScriptAgent"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                start_time = time.time()
                
                result = await self.main_agent.generate_content(
                    task=test_case["task"],
                    request_id=f"test_main_{i}"
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Validate result structure
                if "content" not in result:
                    print(f"❌ No content in result for: {test_case['task'][:30]}...")
                    return False
                
                content = result["content"]
                category_used = result.get("category_used")
                sub_agent_used = result.get("sub_agent_used")
                
                # Check if correct sub-agent was used
                if category_used != test_case["expected_category"]:
                    print(f"❌ Wrong category: Expected {test_case['expected_category']}, got {category_used}")
                    return False
                
                if test_case["expected_agent"] not in str(sub_agent_used):
                    print(f"❌ Wrong sub-agent: Expected {test_case['expected_agent']}, got {sub_agent_used}")
                    return False
                
                print(f"✅ '{test_case['task'][:40]}...'")
                print(f"   Category: {category_used}, Agent: {sub_agent_used}")
                print(f"   Duration: {duration:.2f}s, Content: {len(content)} chars")
                
                # Store performance metrics
                self.performance_metrics.append({
                    "task_type": category_used,
                    "duration": duration,
                    "content_length": len(content),
                    "sub_agent": sub_agent_used
                })
                
            except Exception as e:
                print(f"❌ Main agent test failed for '{test_case['task'][:30]}...': {e}")
                return False
        
        return True
    
    async def test_error_handling(self):
        """Test error handling and fallback mechanisms."""
        print("\n🛡️ Testing Error Handling...")
        
        try:
            # Test with invalid configuration
            from content_writer_v2.config import ContentWriterV2Config, AIProviderConfig
            
            invalid_config = ContentWriterV2Config(
                ai_provider=AIProviderConfig(
                    provider="invalid_provider",
                    model="invalid_model"
                )
            )
            
            # This should handle the error gracefully
            try:
                invalid_agent = ContentWriterMainAgent(invalid_config)
                await invalid_agent.initialize()
                print("❌ Should have failed with invalid configuration")
                return False
            except Exception:
                print("✅ Invalid configuration handled correctly")
            
            # Test with empty task
            try:
                result = await self.main_agent.generate_content(
                    task="",
                    request_id="test_empty_task"
                )
                print("✅ Empty task handled gracefully")
            except Exception as e:
                print(f"✅ Empty task error handled: {type(e).__name__}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False
    
    async def test_performance(self):
        """Test performance benchmarks."""
        print("\n⚡ Testing Performance...")
        
        if not self.performance_metrics:
            print("❌ No performance metrics available")
            return False
        
        # Analyze performance metrics
        total_tests = len(self.performance_metrics)
        avg_duration = sum(m["duration"] for m in self.performance_metrics) / total_tests
        max_duration = max(m["duration"] for m in self.performance_metrics)
        min_duration = min(m["duration"] for m in self.performance_metrics)
        
        print(f"✅ Performance Summary:")
        print(f"   Total tests: {total_tests}")
        print(f"   Average duration: {avg_duration:.2f}s")
        print(f"   Max duration: {max_duration:.2f}s")
        print(f"   Min duration: {min_duration:.2f}s")
        
        # Check if performance meets benchmarks
        if avg_duration > 15:  # 15 second average benchmark
            print(f"❌ Average duration too high: {avg_duration:.2f}s")
            return False
        
        if max_duration > 30:  # 30 second max benchmark
            print(f"❌ Max duration too high: {max_duration:.2f}s")
            return False
        
        print("✅ Performance benchmarks met")
        return True
    
    async def run_all_tests(self):
        """Run all tests in sequence."""
        print("🚀 Starting Content Writer v2 Comprehensive Test Suite")
        print("=" * 60)
        
        tests = [
            ("Environment", self.test_environment),
            ("Task Classification", self.test_task_classification),
            ("Social Media Agent", self.test_social_media_agent),
            ("Blog Agent", self.test_blog_agent),
            ("Script Agent", self.test_script_agent),
            ("Main Agent Integration", self.test_main_agent_integration),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                    self.test_results.append({"test": test_name, "status": "PASSED"})
                else:
                    self.test_results.append({"test": test_name, "status": "FAILED"})
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
                self.test_results.append({"test": test_name, "status": "CRASHED", "error": str(e)})
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if "error" in result:
                print(f"   Error: {result['error']}")
        
        print(f"\nPassed: {passed}/{total} tests")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Content Writer v2 is ready for production.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please review and fix issues.")
        
        return passed == total


async def main():
    """Main test runner."""
    tester = ContentWriterV2Tester()
    
    # Setup
    if not await tester.setup():
        print("❌ Setup failed. Cannot proceed with tests.")
        return
    
    # Run all tests
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())