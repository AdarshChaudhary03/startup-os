"""Simple test to verify JSON parsing fix"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.ceo.ceo_ai_task_analyzer import CEOAITaskAnalyzer


def test_json_parsing():
    """Test the JSON parsing functionality"""
    analyzer = CEOAITaskAnalyzer()
    
    print("Testing JSON parsing functionality...")
    
    # Test 1: Valid JSON
    print("\n1. Testing valid JSON:")
    valid_json = '{"completeness_score": 8, "analysis": {}}'
    result = analyzer._parse_json_response(valid_json, "test")
    print(f"   Result: {result}")
    print(f"   Success: {result is not None}")
    
    # Test 2: JSON with markdown
    print("\n2. Testing JSON wrapped in markdown:")
    markdown_json = '''```json
{
    "completeness_score": 7,
    "analysis": {
        "clarity": {
            "score": 6,
            "assessment": "Good"
        }
    }
}
```'''
    result = analyzer._parse_json_response(markdown_json, "test")
    print(f"   Result: {result}")
    print(f"   Success: {result is not None}")
    
    # Test 3: JSON with extra text
    print("\n3. Testing JSON with surrounding text:")
    text_with_json = '''Here is the analysis:

{"completeness_score": 5, "analysis": {"scope": {"score": 4}}}

That's the result.'''
    result = analyzer._parse_json_response(text_with_json, "test")
    print(f"   Result: {result}")
    print(f"   Success: {result is not None}")
    
    # Test 4: Empty response
    print("\n4. Testing empty response:")
    result = analyzer._parse_json_response("", "test")
    print(f"   Result: {result}")
    print(f"   Success: {result is None}")
    
    # Test 5: Invalid JSON
    print("\n5. Testing invalid JSON:")
    invalid_json = '{"completeness_score": 8, invalid}'
    result = analyzer._parse_json_response(invalid_json, "test")
    print(f"   Result: {result}")
    print(f"   Success: {result is None}")
    
    # Test 6: Fallback questions
    print("\n6. Testing intelligent fallback questions:")
    analysis = {
        "completeness_score": 4,
        "analysis": {
            "clarity": {"score": 3, "missing_elements": ["goal", "outcome"]},
            "scope": {"score": 5, "missing_elements": ["boundaries"]},
            "requirements": {"score": 2, "missing_elements": ["features", "specs"]}
        }
    }
    questions = analyzer._get_default_questions(analysis)
    print(f"   Generated {len(questions)} questions")
    for q in questions:
        print(f"   - {q['question']} (Category: {q['category']}, Priority: {q['priority']})")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_json_parsing()
