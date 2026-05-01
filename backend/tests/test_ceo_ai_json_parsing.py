"""Comprehensive test cases for CEO AI task analyzer JSON parsing fix"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from src.agents.ceo.ceo_ai_task_analyzer import CEOAITaskAnalyzer


class TestCEOAIJsonParsing:
    """Test suite for JSON parsing improvements in CEO AI task analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a CEOAITaskAnalyzer instance for testing"""
        return CEOAITaskAnalyzer()
    
    def test_parse_json_response_valid_json(self, analyzer):
        """Test parsing valid JSON response"""
        valid_json = '{"completeness_score": 8, "analysis": {}}'
        result = analyzer._parse_json_response(valid_json, "test")
        assert result is not None
        assert result["completeness_score"] == 8
    
    def test_parse_json_response_with_markdown(self, analyzer):
        """Test parsing JSON wrapped in markdown code blocks"""
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
        assert result is not None
        assert result["completeness_score"] == 7
        assert result["analysis"]["clarity"]["score"] == 6
    
    def test_parse_json_response_with_extra_text(self, analyzer):
        """Test parsing JSON with surrounding text"""
        text_with_json = '''Here is the analysis:

{"completeness_score": 5, "analysis": {"scope": {"score": 4}}}

That's the result.'''
        result = analyzer._parse_json_response(text_with_json, "test")
        assert result is not None
        assert result["completeness_score"] == 5
    
    def test_parse_json_response_with_bom(self, analyzer):
        """Test parsing JSON with BOM character"""
        json_with_bom = '\ufeff{"completeness_score": 9}'
        result = analyzer._parse_json_response(json_with_bom, "test")
        assert result is not None
        assert result["completeness_score"] == 9
    
    def test_parse_json_response_empty(self, analyzer):
        """Test parsing empty response"""
        result = analyzer._parse_json_response("", "test")
        assert result is None
    
    def test_parse_json_response_invalid(self, analyzer):
        """Test parsing invalid JSON"""
        invalid_json = '{"completeness_score": 8, invalid}'
        result = analyzer._parse_json_response(invalid_json, "test")
        assert result is None
    
    def test_parse_json_response_nested_json(self, analyzer):
        """Test parsing nested JSON structures"""
        nested_json = '''{
            "completeness_score": 6,
            "analysis": {
                "clarity": {
                    "score": 5,
                    "missing_elements": ["goal definition", "expected outcome"]
                }
            },
            "questions": [
                {
                    "id": "q1",
                    "question": "What is the goal?"
                }
            ]
        }'''
        result = analyzer._parse_json_response(nested_json, "test")
        assert result is not None
        assert len(result["analysis"]["clarity"]["missing_elements"]) == 2
        assert len(result["questions"]) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_task_completeness_with_markdown_response(self, analyzer):
        """Test analyze_task_completeness handling markdown responses"""
        with patch('src.services.ai_service.ai_service.generate_content') as mock_generate:
            # Simulate Groq returning markdown-wrapped JSON
            mock_generate.return_value = '''```json
{
    "completeness_score": 4,
    "analysis": {
        "clarity": {"score": 3, "assessment": "Vague", "missing_elements": ["specific goal"]}
    },
    "overall_assessment": "Task needs clarification",
    "key_missing_information": ["goal", "scope"]
}
```'''
            
            result = await analyzer._analyze_task_completeness("vague task", "test-session")
            assert result["completeness_score"] == 4
            assert result["analysis"]["clarity"]["score"] == 3
    
    def test_get_default_questions_intelligent_fallback(self, analyzer):
        """Test intelligent fallback question generation"""
        # Simulate analysis with low scores
        analysis = {
            "completeness_score": 4,
            "analysis": {
                "clarity": {"score": 3, "missing_elements": ["goal", "outcome"]},
                "scope": {"score": 5, "missing_elements": ["boundaries"]},
                "requirements": {"score": 2, "missing_elements": ["features", "specs"]}
            }
        }
        
        questions = analyzer._get_default_questions(analysis)
        assert len(questions) >= 3
        
        # Check that questions target low-scoring areas
        categories = [q["category"] for q in questions]
        assert "requirements" in categories  # Lowest score
        assert "clarity" in categories  # Second lowest
        
        # Check priority assignment
        for q in questions:
            if q["category"] == "requirements":
                assert q["priority"] == "high"  # Score < 4
    
    def test_get_default_questions_no_analysis(self, analyzer):
        """Test fallback questions when no analysis is available"""
        questions = analyzer._get_default_questions(None)
        assert len(questions) == 3
        assert all(q["priority"] == "high" for q in questions)
    
    @pytest.mark.asyncio
    async def test_full_flow_with_json_parsing_recovery(self, analyzer):
        """Test full analysis flow with JSON parsing recovery"""
        with patch('src.services.ai_service.ai_service.generate_content') as mock_generate:
            # First call returns malformed JSON, should fall back to default
            mock_generate.side_effect = [
                'Invalid JSON response',  # Will fail parsing
                '''```json
{
    "questions": [
        {"id": "q1", "question": "What is the goal?", "category": "clarity", "priority": "high"}
    ]
}
```''',  # Valid question generation
            ]
            
            result = await analyzer.analyze_task("test task", "session-123")
            
            # Should get default analysis due to parsing failure
            assert result["state"] == "awaiting_answers"
            assert "questions" in result
            assert result["completeness_score"] == 5  # Default score


def run_tests():
    """Run all tests"""
    pytest.main(["-v", __file__])


if __name__ == "__main__":
    run_tests()
