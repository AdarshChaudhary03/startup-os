#!/usr/bin/env python3
"""
Test script for CEO Learning System

This script tests the CEO learning system functionality including:
1. Learning rule initialization
2. Agent response processing
3. Output passing between agents
4. Learning insights and statistics
"""

import json
import asyncio
from datetime import datetime
from ceo_agent import ceo_agent
from ceo_learning_system import ceo_learning_system, initialize_first_learning


def test_learning_system_initialization():
    """Test learning system initialization"""
    print("\n=== Testing CEO Learning System Initialization ===")
    
    # Initialize first learning rule
    initialize_first_learning()
    
    # Check if the rule was created
    rule = ceo_learning_system.get_delegation_rule("content_writer", "social_media_publisher")
    
    if rule:
        print("✅ First learning rule initialized successfully")
        print(f"   Rule: {rule['rule'][:100]}...")
        print(f"   Pass Output: {rule['pass_output']}")
        print(f"   Output Field: {rule['output_field']}")
    else:
        print("❌ First learning rule not found")
    
    # Get learning statistics
    stats = ceo_learning_system.get_learning_stats()
    print(f"\n📊 Learning Statistics:")
    print(f"   Total Delegation Patterns: {stats['total_delegation_patterns']}")
    print(f"   Total Output Rules: {stats['total_output_rules']}")
    print(f"   Created At: {stats['created_at']}")
    
    return rule is not None


def test_content_writer_response_processing():
    """Test processing Content Writer response"""
    print("\n=== Testing Content Writer Response Processing ===")
    
    # Sample Content Writer response (from user's example)
    content_writer_response = {
        "request_id": "723aa211-3b3e-4832-835f-096c070dfcc0",
        "agent_id": "content_writer",
        "agent_name": "Content Writer",
        "team_id": "marketing",
        "team_name": "Marketing",
        "task": "create a blog on GenAI in 100 words",
        "output": """# Unlocking the Potential of GenAI: Revolutionizing the Future of Technology

The concept of Generative Artificial Intelligence (GenAI) has been gaining significant attention in recent years, and its importance is expected to continue growing as technology advances. In this blog post, we will delve into the world of GenAI, exploring its definition, key features, applications, and future potential. We will also discuss the benefits and challenges of using GenAI, as well as the ethical considerations and regulatory frameworks that are essential for its development and use.

## What is GenAI?

GenAI refers to a type of artificial intelligence that is capable of generating new content, such as text, images, or music, based on a given input or prompt. This technology has the potential to revolutionize various industries, from healthcare and finance to education and entertainment. At its core, GenAI is a subset of artificial intelligence that focuses on creative generation, using complex algorithms and machine learning models to produce unique and innovative outputs.

### History and Evolution

The origins of GenAI can be traced back to the early days of artificial intelligence, when researchers began exploring the potential of machine learning and deep learning. Over the years, GenAI has evolved significantly, with major milestones including the development of Generative Adversarial Networks (GANs) and Variational Autoencoders (VAEs). These advancements have enabled GenAI to produce high-quality, realistic outputs that are often indistinguishable from those created by humans.

## Applications of GenAI

GenAI has numerous applications across various industries, including:

* **Healthcare**: GenAI can be used to generate synthetic medical images, helping to improve diagnosis accuracy and reduce the need for costly and invasive procedures.
* **Finance**: GenAI can be used to generate financial reports, predictions, and analysis, helping to streamline decision-making and reduce the risk of human error.
* **Education**: GenAI can be used to generate personalized learning materials, such as customized textbooks and educational videos, helping to improve student engagement and outcomes.

### Benefits and Challenges

The benefits of using GenAI are numerous, including:

* **Increased efficiency**: GenAI can automate tasks that would otherwise require significant human effort and time.
* **Improved accuracy**: GenAI can produce outputs that are free from human bias and error.
* **Enhanced creativity**: GenAI can generate novel and innovative solutions that may not have been possible for humans to conceive.

However, there are also challenges and limitations associated with implementing GenAI, including:

* **Data quality**: GenAI requires high-quality, diverse, and well-annotated data to produce accurate and reliable outputs.
* **Explainability**: GenAI models can be complex and difficult to interpret, making it challenging to understand the decision-making process behind their outputs.
* **Ethical considerations**: GenAI raises ethical concerns, such as the potential for job displacement, bias, and misuse.

## Future of GenAI

As GenAI continues to evolve, we can expect to see significant advancements in its capabilities and applications. Emerging trends and technologies, such as Explainable AI (XAI) and Transfer Learning, are expected to play a major role in shaping the future of GenAI. The potential impact of GenAI on society and the future of work is substantial, with potential benefits including:

* **Improved productivity**: GenAI can automate routine and repetitive tasks, freeing up humans to focus on more creative and strategic work.
* **Enhanced innovation**: GenAI can generate novel solutions and ideas, helping to drive innovation and progress.
* **Increased accessibility**: GenAI can provide personalized assistance and support, helping to improve accessibility and inclusivity.

### Ethics and Responsibility

As GenAI becomes more prevalent, it is essential to address the ethical considerations and responsibilities associated with its development and use. This includes:

* **Transparency**: GenAI models should be transparent and explainable, with clear documentation and annotation of their decision-making processes.
* **Accountability**: Developers and users of GenAI should be held accountable for its outputs and any potential harm caused.
* **Regulatory frameworks**: Governments and regulatory bodies should establish frameworks to govern the development and use of GenAI, ensuring that it is used responsibly and for the benefit of society.

In conclusion, GenAI has the potential to revolutionize the future of technology, with significant implications for various industries and society as a whole. As we continue to explore and develop this technology, it is essential to prioritize ethics, responsibility, and transparency.

To learn more about GenAI and its applications, we encourage you to explore resources such as research papers, online courses, and industry reports. Joining a community or forum related to GenAI can also provide valuable opportunities for networking and knowledge-sharing. Take the first step today and discover the exciting possibilities of GenAI.""",
        "success": True,
        "duration_ms": 6073,
        "timestamp": "2026-04-29T12:22:09.966977+00:00",
        "error": None,
        "metadata": None
    }
    
    # Test workflow sequence
    workflow_sequence = ["content_writer", "social_media_publisher"]
    original_task = "Create marketing content for GenAI"
    
    # Process agent completion
    result = ceo_agent.process_agent_completion(
        agent_response=content_writer_response,
        workflow_sequence=workflow_sequence,
        original_task=original_task
    )
    
    print(f"✅ CEO Processing Result:")
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    print(f"   Next Agent: {result.get('next_agent')}")
    
    if result['status'] == 'continue':
        delegation_info = result['delegation_info']
        print(f"\n🎯 Delegation Information:")
        print(f"   Learning Rule Used: {delegation_info['used_learning_rule']}")
        print(f"   Source Output Included: {delegation_info['source_output_included']}")
        print(f"   Learning Applied: {delegation_info['learning_applied']}")
        print(f"   Task Preview: {delegation_info['task'][:200]}...")
        
        if delegation_info['source_output_included']:
            print(f"   Source Output Preview: {delegation_info.get('source_output_preview', 'N/A')}")
    
    return result['status'] == 'continue' and result['delegation_info']['used_learning_rule']


def test_output_extraction():
    """Test output extraction from agent responses"""
    print("\n=== Testing Output Extraction ===")
    
    # Test with dict response
    dict_response = {
        "output": "This is the blog content from Content Writer",
        "success": True
    }
    
    extracted = ceo_learning_system.extract_agent_output(dict_response, "output")
    print(f"✅ Dict Extraction: {extracted[:50]}...")
    
    # Test with JSON string response
    json_response = json.dumps({
        "output": "This is JSON string content",
        "success": True
    })
    
    extracted_json = ceo_learning_system.extract_agent_output(json_response, "output")
    print(f"✅ JSON String Extraction: {extracted_json[:50]}...")
    
    return len(extracted) > 0 and len(extracted_json) > 0


def test_task_formatting():
    """Test task formatting with previous output"""
    print("\n=== Testing Task Formatting ===")
    
    original_task = "Create social media posts"
    source_output = "# GenAI Blog\n\nThis is a comprehensive blog about GenAI technology..."
    target_agent = "social_media_publisher"
    
    formatted_task = ceo_learning_system.format_task_with_output(
        original_task, source_output, target_agent
    )
    
    print(f"✅ Formatted Task:")
    print(f"   Original: {original_task}")
    print(f"   Formatted: {formatted_task[:200]}...")
    
    # Check if source output is included
    includes_output = source_output[:50] in formatted_task
    print(f"   Includes Source Output: {includes_output}")
    
    return includes_output


def test_learning_insights():
    """Test learning insights and statistics"""
    print("\n=== Testing Learning Insights ===")
    
    insights = ceo_agent.get_learning_insights()
    
    print(f"✅ Learning Insights:")
    print(f"   Status: {insights['learning_status']}")
    print(f"   Active Rules: {insights['active_rules']}")
    print(f"   Total Patterns: {len(insights['delegation_patterns'])}")
    
    if insights['delegation_patterns']:
        first_pattern = insights['delegation_patterns'][0]
        print(f"   First Pattern: {first_pattern['source_agent']} -> {first_pattern['target_agent']}")
        print(f"   Usage Count: {first_pattern['usage_count']}")
    
    return insights['learning_status'] == 'active' and insights['active_rules'] > 0


def test_should_pass_output():
    """Test output passing decision logic"""
    print("\n=== Testing Output Passing Logic ===")
    
    # Test Content Writer -> Social Media Publisher (should pass)
    should_pass_1 = ceo_learning_system.should_pass_output("content_writer", "social_media_publisher")
    print(f"✅ Content Writer -> Social Media Publisher: {should_pass_1}")
    
    # Test unknown agents (should not pass)
    should_pass_2 = ceo_learning_system.should_pass_output("unknown_agent", "another_agent")
    print(f"✅ Unknown -> Another: {should_pass_2}")
    
    # Test output field retrieval
    output_field = ceo_learning_system.get_output_field("content_writer", "social_media_publisher")
    print(f"✅ Output Field: {output_field}")
    
    return should_pass_1 and not should_pass_2 and output_field == "output"


def run_all_tests():
    """Run all CEO learning system tests"""
    print("🚀 Starting CEO Learning System Tests")
    print("=" * 50)
    
    tests = [
        ("Learning System Initialization", test_learning_system_initialization),
        ("Content Writer Response Processing", test_content_writer_response_processing),
        ("Output Extraction", test_output_extraction),
        ("Task Formatting", test_task_formatting),
        ("Learning Insights", test_learning_insights),
        ("Output Passing Logic", test_should_pass_output)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ ERROR: {test_name} - {str(e)}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, error in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if error:
            print(f"   Error: {error}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CEO Learning System is working correctly.")
    else:
        print(f"⚠️  {total - passed} tests failed. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
