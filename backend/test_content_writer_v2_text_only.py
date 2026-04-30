#!/usr/bin/env python3
"""
Test script to verify Content Writer v2 generates text-only content without emojis.
This script tests all sub-agents to ensure they produce clean, text-only output.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_writer_v2.config import (
    ContentWriterV2Config, 
    SocialPlatform, 
    ContentFormat, 
    ToneStyle
)
from content_writer_v2.sub_agents.social_media import SocialMediaAgent
from content_writer_v2.sub_agents.marketing import MarketingCopyAgent
from content_writer_v2.sub_agents.blog import BlogAgent
from content_writer_v2.sub_agents.script import ScriptAgent
from content_writer_v2.sub_agents.technical import TechnicalWritingAgent


def has_emojis(text: str) -> bool:
    """Check if text contains emojis or special unicode characters."""
    for char in text:
        if ord(char) > 127:  # Non-ASCII characters (likely emojis)
            return True
    return False


def analyze_content(content: str, content_type: str) -> dict:
    """Analyze content for text-only compliance."""
    has_emoji = has_emojis(content)
    word_count = len(content.split())
    char_count = len(content)
    
    return {
        "content_type": content_type,
        "has_emojis": has_emoji,
        "word_count": word_count,
        "character_count": char_count,
        "is_text_only": not has_emoji,
        "preview": content[:100] + "..." if len(content) > 100 else content
    }


async def test_social_media_agent():
    """Test social media agent for text-only content."""
    print("\n=== Testing Social Media Agent ===")
    
    # Test with default config (should have emojis disabled)
    config = ContentWriterV2Config()
    agent = SocialMediaAgent(config)
    
    test_cases = [
        {
            "platform": SocialPlatform.INSTAGRAM,
            "task": "Create a post about healthy eating tips",
            "include_emojis": None  # Use default
        },
        {
            "platform": SocialPlatform.FACEBOOK,
            "task": "Announce a new product launch",
            "include_emojis": False  # Explicitly disable
        },
        {
            "platform": SocialPlatform.TWITTER,
            "task": "Share a motivational quote",
            "include_emojis": True  # Try to enable (should be overridden)
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases):
        try:
            print(f"\nTest {i+1}: {test_case['platform'].value} - {test_case['task'][:30]}...")
            
            result = await agent.generate_content(
                task=test_case["task"],
                request_id=f"test_social_{i+1}",
                platform=test_case["platform"],
                include_emojis=test_case["include_emojis"]
            )
            
            content = result["content"]
            analysis = analyze_content(content, f"Social Media - {test_case['platform'].value}")
            results.append(analysis)
            
            print(f"✓ Generated {analysis['word_count']} words")
            print(f"✓ Text-only: {analysis['is_text_only']}")
            if analysis['has_emojis']:
                print(f"⚠️  WARNING: Contains emojis!")
            print(f"Preview: {analysis['preview']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"content_type": f"Social Media - {test_case['platform'].value}", "error": str(e)})
    
    return results


async def test_marketing_agent():
    """Test marketing copy agent for text-only content."""
    print("\n=== Testing Marketing Copy Agent ===")
    
    agent = MarketingCopyAgent()
    
    test_cases = [
        {
            "copy_type": "ad_copy",
            "task": "Create an ad for a fitness app",
            "product_name": "FitTracker Pro"
        },
        {
            "copy_type": "email_copy",
            "task": "Welcome email for new subscribers",
            "product_name": "Newsletter"
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases):
        try:
            print(f"\nTest {i+1}: {test_case['copy_type']} - {test_case['task'][:30]}...")
            
            result = await agent.generate_content(
                task=test_case["task"],
                request_id=f"test_marketing_{i+1}",
                copy_type=test_case["copy_type"],
                product_name=test_case["product_name"]
            )
            
            content = result["content"]
            analysis = analyze_content(content, f"Marketing - {test_case['copy_type']}")
            results.append(analysis)
            
            print(f"✓ Generated {analysis['word_count']} words")
            print(f"✓ Text-only: {analysis['is_text_only']}")
            if analysis['has_emojis']:
                print(f"⚠️  WARNING: Contains emojis!")
            print(f"Preview: {analysis['preview']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"content_type": f"Marketing - {test_case['copy_type']}", "error": str(e)})
    
    return results


async def test_blog_agent():
    """Test blog agent for text-only content."""
    print("\n=== Testing Blog Agent ===")
    
    agent = BlogAgent()
    
    try:
        print("\nTest: Blog post about remote work productivity")
        
        result = await agent.generate_content(
            task="Write a blog post about productivity tips for remote workers",
            request_id="test_blog_1",
            word_count=500,
            tone=ToneStyle.PROFESSIONAL
        )
        
        content = result["content"]
        analysis = analyze_content(content, "Blog Post")
        
        print(f"✓ Generated {analysis['word_count']} words")
        print(f"✓ Text-only: {analysis['is_text_only']}")
        if analysis['has_emojis']:
            print(f"⚠️  WARNING: Contains emojis!")
        print(f"Preview: {analysis['preview']}")
        
        return [analysis]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [{"content_type": "Blog Post", "error": str(e)}]


async def test_script_agent():
    """Test script agent for text-only content."""
    print("\n=== Testing Script Agent ===")
    
    agent = ScriptAgent()
    
    try:
        print("\nTest: Instagram Reel script about cooking tips")
        
        result = await agent.generate_content(
            task="Create a script for a cooking tips reel",
            request_id="test_script_1",
            script_type="reel",
            duration_seconds=30
        )
        
        content = result["content"]
        analysis = analyze_content(content, "Script - Reel")
        
        print(f"✓ Generated {analysis['word_count']} words")
        print(f"✓ Text-only: {analysis['is_text_only']}")
        if analysis['has_emojis']:
            print(f"⚠️  WARNING: Contains emojis!")
        print(f"Preview: {analysis['preview']}")
        
        return [analysis]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [{"content_type": "Script - Reel", "error": str(e)}]


async def test_technical_agent():
    """Test technical writing agent for text-only content."""
    print("\n=== Testing Technical Writing Agent ===")
    
    agent = TechnicalWritingAgent()
    
    try:
        print("\nTest: API documentation for user authentication")
        
        result = await agent.generate_content(
            task="Document the user authentication API endpoints",
            request_id="test_technical_1",
            doc_type="api_docs",
            programming_language="Python"
        )
        
        content = result["content"]
        analysis = analyze_content(content, "Technical - API Docs")
        
        print(f"✓ Generated {analysis['word_count']} words")
        print(f"✓ Text-only: {analysis['is_text_only']}")
        if analysis['has_emojis']:
            print(f"⚠️  WARNING: Contains emojis!")
        print(f"Preview: {analysis['preview']}")
        
        return [analysis]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [{"content_type": "Technical - API Docs", "error": str(e)}]


async def main():
    """Run all tests and generate summary report."""
    print("🧪 Content Writer v2 Text-Only Content Test Suite")
    print("=" * 60)
    
    all_results = []
    
    # Run all agent tests
    try:
        social_results = await test_social_media_agent()
        all_results.extend(social_results)
    except Exception as e:
        print(f"❌ Social Media Agent test failed: {e}")
    
    try:
        marketing_results = await test_marketing_agent()
        all_results.extend(marketing_results)
    except Exception as e:
        print(f"❌ Marketing Agent test failed: {e}")
    
    try:
        blog_results = await test_blog_agent()
        all_results.extend(blog_results)
    except Exception as e:
        print(f"❌ Blog Agent test failed: {e}")
    
    try:
        script_results = await test_script_agent()
        all_results.extend(script_results)
    except Exception as e:
        print(f"❌ Script Agent test failed: {e}")
    
    try:
        technical_results = await test_technical_agent()
        all_results.extend(technical_results)
    except Exception as e:
        print(f"❌ Technical Agent test failed: {e}")
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 SUMMARY REPORT")
    print("=" * 60)
    
    total_tests = len(all_results)
    text_only_count = sum(1 for r in all_results if r.get('is_text_only', False))
    error_count = sum(1 for r in all_results if 'error' in r)
    
    print(f"Total tests run: {total_tests}")
    print(f"Text-only compliant: {text_only_count}")
    print(f"Errors encountered: {error_count}")
    print(f"Success rate: {((text_only_count / max(total_tests - error_count, 1)) * 100):.1f}%")
    
    # Show detailed results
    print("\nDetailed Results:")
    for result in all_results:
        if 'error' in result:
            print(f"❌ {result['content_type']}: ERROR - {result['error']}")
        elif result.get('is_text_only', False):
            print(f"✅ {result['content_type']}: Text-only compliant ({result['word_count']} words)")
        else:
            print(f"⚠️  {result['content_type']}: Contains emojis/special characters")
    
    # Final verdict
    if text_only_count == total_tests - error_count and error_count == 0:
        print("\n🎉 ALL TESTS PASSED! Content Writer v2 is generating text-only content.")
    elif text_only_count == total_tests - error_count:
        print(f"\n⚠️  TESTS PASSED with {error_count} errors. Text-only content is working where tested.")
    else:
        print(f"\n❌ TESTS FAILED! {total_tests - text_only_count - error_count} tests still generating emojis.")


if __name__ == "__main__":
    asyncio.run(main())
