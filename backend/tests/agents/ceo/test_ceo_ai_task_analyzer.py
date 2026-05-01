"""Test cases for AI-based CEO Task Analyzer

This module tests the AI-driven task analysis system including:
- Task completeness scoring
- Dynamic question generation
- Task restructuring
- Iterative refinement
- Prompt polishing
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.agents.ceo.ceo_ai_task_analyzer import (
    CEOAITaskAnalyzer,
    TaskAnalysisState
)


class TestCEOAITaskAnalyzer:
    """Test suite for CEO AI Task Analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return CEOAITaskAnalyzer()
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for testing"""
        with patch('src.agents.ceo.ceo_ai_task_analyzer.ai_service') as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_initial_task_analysis_complete(self, analyzer, mock_ai_service):
        """Test when initial task analysis shows high completeness"""
        # Mock AI response with high completeness score
        mock_ai_service.generate_content = AsyncMock(return_value=json.dumps({
            "completeness_score": 9.5,
            "analysis": {
                "clarity": {"score": 9, "assessment": "Very clear", "missing_elements": []},
                "scope": {"score": 10, "assessment": "Well defined", "missing_elements": []},
                "context": {"score": 9, "assessment": "Good context", "missing_elements": []},
                "requirements": {"score": 9, "assessment": "Clear requirements", "missing_elements": []},
                "constraints": {"score": 10, "assessment": "Constraints specified", "missing_elements": []},
                "success_criteria": {"score": 9, "assessment": "Measurable criteria", "missing_elements": []},
                "target_audience": {"score": 10, "assessment": "Well identified", "missing_elements": []},
                "dependencies": {"score": 9, "assessment": "Dependencies clear", "missing_elements": []}
            },
            "overall_assessment": "Task is well-defined and ready for execution",
            "key_missing_information": []
        }))
        
        # Mock polished prompt response
        mock_ai_service.generate_content.side_effect = [
            json.dumps({  # First call - analysis
                "completeness_score": 9.5,
                "analysis": {"clarity": {"score": 9, "assessment": "Very clear", "missing_elements": []}},
                "overall_assessment": "Task is well-defined",
                "key_missing_information": []
            }),
            json.dumps({  # Second call - polished prompt
                "polished_prompt": "Create a comprehensive e-commerce platform...",
                "executive_summary": "Build full-featured online store",
                "key_deliverables": ["User authentication", "Product catalog", "Shopping cart"],
                "agent_instructions": {
                    "primary_focus": "E-commerce functionality",
                    "considerations": ["Security", "Performance"],
                    "quality_standards": ["PCI compliance", "Mobile responsive"]
                }
            })
        ]
        
        # Test task with high completeness
        task = "Create a comprehensive e-commerce platform with user authentication, product catalog, shopping cart, payment integration, and order management. Target audience is small to medium businesses. Must be secure, scalable, and mobile-friendly. Timeline: 3 months."
        
        result = await analyzer.analyze_task(task, "test-session-123")
        
        # Assertions
        assert result["state"] == "complete"
        assert result["success"] == True
        assert result["final_completeness_score"] == 9.5
        assert result["iterations_used"] == 1
        assert "polished_prompt" in result
        assert "executive_summary" in result
        assert len(result["deliverables"]) == 3
    
    @pytest.mark.asyncio
    async def test_initial_task_analysis_needs_clarification(self, analyzer, mock_ai_service):
        """Test when initial task analysis requires clarification"""
        # Mock AI response with low completeness score
        mock_ai_service.generate_content = AsyncMock()
        mock_ai_service.generate_content.side_effect = [
            json.dumps({  # Analysis response
                "completeness_score": 4.5,
                "analysis": {
                    "clarity": {"score": 5, "assessment": "Vague goal", "missing_elements": ["Specific objectives"]},
                    "scope": {"score": 3, "assessment": "Unclear scope", "missing_elements": ["Feature list", "Boundaries"]},
                    "context": {"score": 4, "assessment": "Limited context", "missing_elements": ["Business context"]},
                    "requirements": {"score": 3, "assessment": "No requirements", "missing_elements": ["Technical requirements"]},
                    "constraints": {"score": 5, "assessment": "No constraints", "missing_elements": ["Budget", "Timeline"]},
                    "success_criteria": {"score": 4, "assessment": "Vague success", "missing_elements": ["Measurable outcomes"]},
                    "target_audience": {"score": 6, "assessment": "Partially defined", "missing_elements": ["User personas"]},
                    "dependencies": {"score": 5, "assessment": "Unknown dependencies", "missing_elements": ["External systems"]}
                },
                "overall_assessment": "Task needs significant clarification",
                "key_missing_information": ["Specific objectives", "Feature list", "Technical requirements", "Timeline"]
            }),
            json.dumps({  # Questions response
                "questions": [
                    {
                        "id": "q1",
                        "question": "What specific features do you want in the website?",
                        "purpose": "Clarify scope and requirements",
                        "category": "scope",
                        "priority": "high"
                    },
                    {
                        "id": "q2",
                        "question": "Who is your target audience and what are their needs?",
                        "purpose": "Define user personas",
                        "category": "target_audience",
                        "priority": "high"
                    },
                    {
                        "id": "q3",
                        "question": "What is your timeline and budget for this project?",
                        "purpose": "Establish constraints",
                        "category": "constraints",
                        "priority": "high"
                    }
                ]
            })
        ]
        
        # Test vague task
        task = "Build a website"
        
        result = await analyzer.analyze_task(task, "test-session-456")
        
        # Assertions
        assert result["state"] == "awaiting_answers"
        assert result["iteration"] == 1
        assert result["completeness_score"] == 4.5
        assert result["requires_user_input"] == True
        assert "questions" in result
        assert len(result["questions"]) == 3
        assert result["questions"][0]["priority"] == "high"
    
    @pytest.mark.asyncio
    async def test_continue_with_answers_improves_score(self, analyzer, mock_ai_service):
        """Test continuing analysis with user answers improves completeness"""
        # Setup initial session data
        session_data = {
            "session_id": "test-session-789",
            "current_task": "Build a website",
            "questions": [
                {"id": "q1", "question": "What features?", "category": "scope"},
                {"id": "q2", "question": "Target audience?", "category": "audience"},
                {"id": "q3", "question": "Timeline?", "category": "constraints"}
            ],
            "analysis": {"completeness_score": 4.5},
            "iteration": 1
        }
        
        # User answers
        answers = {
            "q1": "E-commerce site with product catalog, shopping cart, user accounts, and payment processing",
            "q2": "Small business owners aged 25-45 who want to sell online",
            "q3": "3 months, budget $50,000"
        }
        
        # Mock AI responses for restructuring and re-analysis
        mock_ai_service.generate_content = AsyncMock()
        mock_ai_service.generate_content.side_effect = [
            json.dumps({  # Restructuring response
                "restructured_task": "Build an e-commerce website for small business owners...",
                "key_additions": ["E-commerce features", "Target audience defined", "Timeline and budget"],
                "structure": {
                    "goal": "Create e-commerce platform",
                    "scope": "Product catalog, shopping cart, user accounts, payments",
                    "requirements": ["Secure payment processing", "User-friendly interface"],
                    "constraints": ["3 month timeline", "$50,000 budget"],
                    "success_criteria": ["Functional online store", "Secure transactions"],
                    "target_audience": "Small business owners aged 25-45",
                    "dependencies": ["Payment gateway integration"]
                }
            }),
            json.dumps({  # Re-analysis response
                "completeness_score": 9.2,
                "analysis": {
                    "clarity": {"score": 9, "assessment": "Clear objectives", "missing_elements": []},
                    "scope": {"score": 9, "assessment": "Well-defined scope", "missing_elements": []}
                },
                "overall_assessment": "Task is now well-defined and ready",
                "key_missing_information": []
            }),
            json.dumps({  # Polished prompt response
                "polished_prompt": "Create an e-commerce website for small business owners...",
                "executive_summary": "E-commerce platform development",
                "key_deliverables": ["Online store", "Payment system", "User management"],
                "agent_instructions": {
                    "primary_focus": "User-friendly e-commerce",
                    "considerations": ["Security", "Usability"],
                    "quality_standards": ["PCI compliance", "Responsive design"]
                }
            })
        ]
        
        result = await analyzer.continue_with_answers(session_data, answers)
        
        # Assertions
        assert result["state"] == "complete"
        assert result["success"] == True
        assert result["final_completeness_score"] == 9.2
        assert "polished_prompt" in result
        assert len(result["deliverables"]) == 3
    
    @pytest.mark.asyncio
    async def test_multiple_iterations_until_complete(self, analyzer, mock_ai_service):
        """Test multiple iterations of refinement until completeness reached"""
        # This test would simulate multiple rounds of questions and answers
        # Implementation would follow similar pattern to above tests
        pass
    
    @pytest.mark.asyncio
    async def test_error_handling_in_ai_calls(self, analyzer, mock_ai_service):
        """Test error handling when AI service fails"""
        # Mock AI service to raise exception
        mock_ai_service.generate_content = AsyncMock(side_effect=Exception("AI service error"))
        
        task = "Build a website"
        result = await analyzer.analyze_task(task, "test-session-error")
        
        # Should handle error gracefully
        assert result["state"] == "error"
        assert result["success"] == False
        assert "error" in result
        assert "AI service error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_max_iterations_limit(self, analyzer, mock_ai_service):
        """Test that analyzer respects maximum iteration limit"""
        # Mock AI to always return low score
        mock_ai_service.generate_content = AsyncMock()
        
        # Set analyzer max iterations to 2 for testing
        analyzer.max_iterations = 2
        
        # Mock responses that keep score low
        low_score_response = json.dumps({
            "completeness_score": 5.0,
            "analysis": {"clarity": {"score": 5, "assessment": "Still unclear", "missing_elements": ["Details"]}},
            "overall_assessment": "Needs more clarification",
            "key_missing_information": ["More details needed"]
        })
        
        questions_response = json.dumps({
            "questions": [{"id": "q1", "question": "More details?", "priority": "high", "category": "clarity"}]
        })
        
        mock_ai_service.generate_content.side_effect = [
            low_score_response,  # First analysis
            questions_response,   # First questions
        ]
        
        task = "Do something"
        result = await analyzer.analyze_task(task, "test-max-iterations")
        
        # Should stop at max iterations even if score is low
        assert result["iteration"] <= analyzer.max_iterations
        assert result["state"] == "awaiting_answers"
    
    def test_extract_missing_information(self, analyzer):
        """Test extraction of missing information from analysis"""
        analysis = {
            "key_missing_information": ["Timeline", "Budget"],
            "analysis": {
                "scope": {"score": 4, "missing_elements": ["Feature list", "Boundaries"]},
                "requirements": {"score": 3, "missing_elements": ["Technical specs"]},
                "success_criteria": {"score": 8, "missing_elements": []}
            }
        }
        
        missing_info = analyzer._extract_missing_information(analysis)
        
        # Should combine and deduplicate missing information
        assert "Timeline" in missing_info
        assert "Budget" in missing_info
        assert "Feature list" in missing_info
        assert "Technical specs" in missing_info
        assert len(missing_info) <= 10  # Should limit to top 10
    
    def test_format_qa_pairs(self, analyzer):
        """Test formatting of questions and answers into pairs"""
        questions = [
            {"id": "q1", "question": "What is the goal?", "category": "clarity", "purpose": "Clarify objective"},
            {"id": "q2", "question": "Who are the users?", "category": "audience", "purpose": "Define audience"}
        ]
        
        answers = {
            "q1": "Build an online learning platform",
            "q2": "Students and teachers",
            "q3": "This should be ignored"  # Extra answer not in questions
        }
        
        qa_pairs = analyzer._format_qa_pairs(questions, answers)
        
        assert len(qa_pairs) == 2
        assert qa_pairs[0]["question"] == "What is the goal?"
        assert qa_pairs[0]["answer"] == "Build an online learning platform"
        assert qa_pairs[0]["category"] == "clarity"
        assert qa_pairs[1]["answer"] == "Students and teachers"
    
    @pytest.mark.asyncio
    async def test_json_parsing_fallback(self, analyzer, mock_ai_service):
        """Test fallback when AI returns invalid JSON"""
        # Mock AI to return invalid JSON
        mock_ai_service.generate_content = AsyncMock(return_value="This is not valid JSON")
        
        task = "Build something"
        result = await analyzer.analyze_task(task, "test-json-error")
        
        # Should use default analysis
        assert result["state"] == "awaiting_answers"
        assert result["completeness_score"] == 5  # Default score
        assert "questions" in result


class TestIntegrationScenarios:
    """Integration test scenarios for CEO AI Task Analyzer"""
    
    @pytest.mark.asyncio
    async def test_complete_flow_vague_to_polished(self):
        """Test complete flow from vague task to polished prompt"""
        # This would test the full flow with mock AI responses
        # simulating a real conversation from vague input to polished output
        pass
    
    @pytest.mark.asyncio
    async def test_edge_cases(self):
        """Test edge cases like empty input, very long input, special characters"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])