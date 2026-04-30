import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Import modules to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ceo_conversation_flow import CEOConversationFlow, ConversationState
from ceo_chat_interface import CEOChatInterface, ChatSessionState
from ceo_requirements_analyzer import CEORequirementsAnalyzer
from ceo_agent_planner import CEOAgentPlanner


class TestCEOConversationFlow:
    """Test cases for CEO conversation flow"""
    
    def setup_method(self):
        """Setup for each test"""
        self.flow = CEOConversationFlow()
    
    def test_get_initial_questions_adaptive(self):
        """Test adaptive question generation"""
        # Test with minimal task
        task = "Create a blog post"
        questions = self.flow.get_initial_questions(task, "adaptive")
        
        assert len(questions) >= 3
        assert len(questions) <= 5
        assert all("question" in q for q in questions)
        assert any("purpose" in q["area"] for q in questions)
    
    def test_get_initial_questions_comprehensive(self):
        """Test comprehensive question generation"""
        task = "Build a marketing campaign"
        questions = self.flow.get_initial_questions(task, "comprehensive")
        
        assert len(questions) == 5  # Should ask all areas
        areas = [q["area"] for q in questions]
        assert "purpose" in areas
        assert "audience" in areas
        assert "scope" in areas
    
    def test_get_initial_questions_minimal(self):
        """Test minimal question generation"""
        task = "Write documentation"
        questions = self.flow.get_initial_questions(task, "minimal")
        
        assert len(questions) <= 3
        assert all(q["required"] for q in questions)
    
    def test_analyze_task_completeness(self):
        """Test task completeness analysis"""
        # Complete task
        complete_task = "Create a blog post for developers about Python best practices by next Friday"
        missing = self.flow._analyze_task_completeness(complete_task)
        assert "timeline" not in missing  # Timeline is specified
        
        # Incomplete task
        incomplete_task = "Write something"
        missing = self.flow._analyze_task_completeness(incomplete_task)
        assert "purpose" in missing
        assert "audience" in missing
        assert "timeline" in missing
    
    def test_process_response(self):
        """Test response processing"""
        question_id = "q_purpose_1"
        response = "To educate developers about best practices"
        context = {"responses": {}}
        
        result = self.flow.process_response(question_id, response, context)
        
        assert result["response_valid"]
        assert result["area"] == "purpose"
        assert not result["needs_followup"]  # Good response shouldn't need followup
    
    def test_process_response_needs_followup(self):
        """Test response that needs follow-up"""
        question_id = "q_purpose_1"
        response = "Not sure"
        context = {"responses": {}}
        
        result = self.flow.process_response(question_id, response, context)
        
        assert result["needs_followup"]
        assert result["followup_question"] is not None
    
    def test_generate_requirements_summary(self):
        """Test requirements summary generation"""
        responses = {
            "purpose": "Create educational content",
            "audience": "Python developers",
            "timeline": "2 weeks",
            "scope": "Cover testing, documentation, and code style",
            "constraints": "Keep it under 2000 words"
        }
        
        summary = self.flow.generate_requirements_summary(responses)
        
        assert summary["purpose"] == responses["purpose"]
        assert summary["target_audience"] == responses["audience"]
        assert summary["timeline"] == responses["timeline"]
        assert "success_criteria" in summary
        assert len(summary["success_criteria"]) > 0


class TestCEOChatInterface:
    """Test cases for CEO chat interface"""
    
    def setup_method(self):
        """Setup for each test"""
        self.chat = CEOChatInterface()
    
    def test_start_chat_session(self):
        """Test starting a new chat session"""
        task = "Create a social media campaign"
        user_context = {"company": "TechCorp", "industry": "Software"}
        
        result = self.chat.start_chat_session(task, user_context)
        
        assert "session_id" in result
        assert "greeting" in result
        assert "initial_questions" in result
        assert len(result["initial_questions"]) >= 3
        assert result["max_questions"] == 5
        
        # Verify session was created
        session_id = result["session_id"]
        assert session_id in self.chat.active_sessions
        session = self.chat.active_sessions[session_id]
        assert session["original_task"] == task
        assert session["user_context"] == user_context
    
    def test_process_user_response(self):
        """Test processing user responses"""
        # Start session
        result = self.chat.start_chat_session("Create content")
        session_id = result["session_id"]
        question = result["initial_questions"][0]
        
        # Submit response
        response_result = self.chat.process_user_response(
            session_id,
            question["id"],
            "To educate our users about new features"
        )
        
        assert response_result["action"] in ["ask_next", "ask_followup", "confirm_requirements"]
        assert "message" in response_result
        
        # Verify response was stored
        session = self.chat.active_sessions[session_id]
        assert question["id"] in session["responses"]
    
    def test_process_response_invalid_session(self):
        """Test processing response for invalid session"""
        with pytest.raises(ValueError):
            self.chat.process_user_response("invalid_session_id", "q_1", "response")
    
    def test_confirm_requirements(self):
        """Test requirements confirmation"""
        # Start session and simulate responses
        result = self.chat.start_chat_session("Create a blog post")
        session_id = result["session_id"]
        
        # Simulate having collected responses
        session = self.chat.active_sessions[session_id]
        session["responses"] = {
            "q_purpose_1": "Educate developers",
            "q_audience_1": "Python developers",
            "q_timeline_1": "Next week"
        }
        session["state"] = ChatSessionState.CONFIRMING_REQUIREMENTS
        
        # Confirm requirements
        confirm_result = self.chat.confirm_requirements(session_id, True)
        
        assert confirm_result["action"] == "requirements_complete"
        assert "polished_requirements" in confirm_result
        assert session["state"] == ChatSessionState.COMPLETE
    
    def test_confirm_requirements_with_adjustments(self):
        """Test requirements confirmation with adjustments"""
        # Start session
        result = self.chat.start_chat_session("Create content")
        session_id = result["session_id"]
        session = self.chat.active_sessions[session_id]
        session["state"] = ChatSessionState.CONFIRMING_REQUIREMENTS
        
        # Request adjustments
        adjust_result = self.chat.confirm_requirements(
            session_id,
            False,
            "Please make it more technical"
        )
        
        assert adjust_result["action"] == "requirements_adjusted"
        assert "adjustments" in session["responses"]
    
    def test_get_session_status(self):
        """Test getting session status"""
        # Create session
        result = self.chat.start_chat_session("Test task")
        session_id = result["session_id"]
        
        # Get status
        status = self.chat.get_session_status(session_id)
        
        assert status["session_id"] == session_id
        assert "state" in status
        assert "questions_asked" in status
        assert "created_at" in status
        assert not status["is_complete"]
    
    def test_get_session_status_not_found(self):
        """Test getting status for non-existent session"""
        status = self.chat.get_session_status("non_existent")
        assert status["status"] == "not_found"


class TestCEORequirementsAnalyzer:
    """Test cases for CEO requirements analyzer"""
    
    def setup_method(self):
        """Setup for each test"""
        self.analyzer = CEORequirementsAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_requirements(self):
        """Test comprehensive requirements analysis"""
        task = "Build a web application for task management"
        responses = {
            "purpose": "Help teams track and manage their tasks efficiently",
            "audience": "Small to medium software development teams",
            "scope": "Task creation, assignment, tracking, and reporting",
            "timeline": "3 months",
            "constraints": "Must integrate with existing tools like Jira and Slack"
        }
        context = {"user_context": {"company_size": "50-100"}}
        
        # Mock AI service response
        with patch('ai_service.ai_service.generate_content', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = json.dumps([
                {
                    "id": "FR-001",
                    "description": "User authentication and authorization",
                    "priority": "high",
                    "category": "core",
                    "acceptance_criteria": ["Users can login", "Role-based access"]
                }
            ])
            
            analysis = await self.analyzer.analyze_requirements(
                task, responses, context, "test_request_id"
            )
        
        assert "functional_requirements" in analysis
        assert "non_functional_requirements" in analysis
        assert "technical_specifications" in analysis
        assert "project_scope" in analysis
        assert "priority_level" in analysis
        assert "complexity_assessment" in analysis
        assert "success_metrics" in analysis
        assert "recommendations" in analysis
    
    def test_detect_requirement_patterns(self):
        """Test requirement pattern detection"""
        context = """
        We need a fast and secure system that can scale to handle 
        thousands of concurrent users. The interface should be 
        user-friendly and intuitive.
        """
        
        patterns = self.analyzer._detect_requirement_patterns(context)
        
        assert "performance" in patterns
        assert "security" in patterns
        assert "scalability" in patterns
        assert "usability" in patterns
    
    def test_determine_priority(self):
        """Test priority determination"""
        # Urgent priority
        urgent_responses = {"timeline": "Need this ASAP!"}
        assert self.analyzer._determine_priority(urgent_responses) == "urgent"
        
        # High priority
        high_responses = {"timeline": "This is important, need it soon"}
        assert self.analyzer._determine_priority(high_responses) == "high"
        
        # Low priority
        low_responses = {"timeline": "No rush, whenever you can"}
        assert self.analyzer._determine_priority(low_responses) == "low"
        
        # Default medium
        normal_responses = {"timeline": "In a few weeks"}
        assert self.analyzer._determine_priority(normal_responses) == "medium"
    
    def test_assess_complexity(self):
        """Test complexity assessment"""
        # High complexity
        many_reqs = [{"id": f"FR-{i}"} for i in range(15)]
        many_nf_reqs = [{"id": f"NFR-{i}"} for i in range(8)]
        complexity = self.analyzer._assess_complexity(many_reqs, many_nf_reqs)
        assert complexity["level"] == "high"
        
        # Low complexity
        few_reqs = [{"id": "FR-1"}, {"id": "FR-2"}]
        few_nf_reqs = [{"id": "NFR-1"}]
        complexity = self.analyzer._assess_complexity(few_reqs, few_nf_reqs)
        assert complexity["level"] == "low"
    
    def test_generate_markdown_documentation(self):
        """Test markdown documentation generation"""
        analysis = {
            "priority_level": "high",
            "complexity_assessment": {"level": "medium", "factors": []},
            "functional_requirements": [
                {
                    "id": "FR-001",
                    "description": "User login",
                    "priority": "high",
                    "category": "core",
                    "acceptance_criteria": ["Users can login with email"]
                }
            ],
            "non_functional_requirements": [
                {
                    "id": "NFR-001",
                    "type": "performance",
                    "description": "Fast response time",
                    "metric": "Response time",
                    "target_value": "< 2 seconds"
                }
            ],
            "technical_specifications": {
                "architecture_pattern": "Microservices",
                "technology_stack": {
                    "frontend": ["React"],
                    "backend": ["Python", "FastAPI"]
                }
            },
            "project_scope": {
                "in_scope": ["User management"],
                "out_of_scope": ["Mobile app"],
                "risks": []
            },
            "success_metrics": [
                {
                    "metric": "User adoption",
                    "target": "1000 users in 3 months",
                    "measurement": "Analytics"
                }
            ],
            "recommendations": ["Use cloud infrastructure"]
        }
        
        doc = self.analyzer.generate_documentation(analysis, "markdown")
        
        assert "# Requirements Documentation" in doc
        assert "## Executive Summary" in doc
        assert "## Functional Requirements" in doc
        assert "FR-001" in doc
        assert "## Non-Functional Requirements" in doc
        assert "NFR-001" in doc
        assert "## Technical Specifications" in doc
        assert "Microservices" in doc
        assert "## Success Metrics" in doc


class TestCEOAgentPlanner:
    """Test cases for CEO agent planner"""
    
    def setup_method(self):
        """Setup for each test"""
        self.planner = CEOAgentPlanner()
    
    @pytest.mark.asyncio
    async def test_create_agent_plan(self):
        """Test agent plan creation"""
        requirements = {
            "polished_task": "Create a blog post about Python best practices",
            "objective": "Educate developers",
            "deliverables": ["Blog post", "Code examples"],
            "target_audience": "Python developers",
            "timeline": "1 week"
        }
        
        # Mock AI service
        with patch('ai_service.ai_service.generate_content', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = json.dumps({
                "primary_domain": "content",
                "required_agents": ["content_writer"],
                "agent_rationale": {
                    "content_writer": "Needed to create the blog post"
                },
                "workflow_type": "sequential",
                "dependencies": []
            })
            
            result = await self.planner.create_agent_plan(requirements, "test_request")
        
        assert result["success"]
        assert "plan" in result
        assert "selected_agents" in result
        assert len(result["selected_agents"]) > 0
        assert result["selected_agents"][0]["id"] == "content_writer"
    
    def test_select_agents(self):
        """Test agent selection based on analysis"""
        agent_analysis = {
            "required_agents": ["content_writer", "social_media_publisher"],
            "agent_rationale": {
                "content_writer": "Create content",
                "social_media_publisher": "Publish to social media"
            }
        }
        
        selected = self.planner._select_agents(agent_analysis)
        
        assert len(selected) == 2
        assert any(a["id"] == "content_writer" for a in selected)
        assert any(a["id"] == "social_media_publisher" for a in selected)
        assert all("rationale" in a for a in selected)
    
    def test_determine_workflow(self):
        """Test workflow determination"""
        selected_agents = [
            {"id": "content_writer"},
            {"id": "social_media_publisher"}
        ]
        agent_analysis = {"workflow_type": "sequential"}
        
        workflow = self.planner._determine_workflow(selected_agents, agent_analysis)
        
        assert workflow["type"] == "sequential"
        assert workflow["pattern"] in ["content_creation", "marketing_campaign", "custom"]
        assert len(workflow["sequence"]) == 2
    
    def test_create_execution_plan(self):
        """Test execution plan creation"""
        selected_agents = [
            {
                "id": "content_writer",
                "name": "Content Writer Agent",
                "team": "content",
                "endpoint": "/api/agents/content-writer"
            }
        ]
        workflow = {
            "type": "sequential",
            "pattern": "custom",
            "sequence": ["content_writer"]
        }
        requirements = {
            "polished_task": "Write a blog post",
            "objective": "Educate users"
        }
        
        plan = self.planner._create_execution_plan(
            selected_agents, workflow, requirements
        )
        
        assert "plan_id" in plan
        assert plan["workflow_type"] == "sequential"
        assert plan["total_steps"] == 1
        assert len(plan["steps"]) == 1
        
        step = plan["steps"][0]
        assert step["agent_id"] == "content_writer"
        assert "instructions" in step
        assert "expected_output" in step
        assert "success_criteria" in step
    
    def test_validate_plan(self):
        """Test plan validation"""
        # Valid plan
        valid_plan = {
            "plan_id": "test-123",
            "workflow_type": "sequential",
            "steps": [
                {
                    "agent_id": "content_writer",
                    "instructions": "Write content",
                    "endpoint": "/api/agents/content-writer"
                }
            ]
        }
        
        is_valid, issues = self.planner.validate_plan(valid_plan)
        assert is_valid
        assert len(issues) == 0
        
        # Invalid plan - missing required fields
        invalid_plan = {
            "workflow_type": "sequential",
            "steps": []
        }
        
        is_valid, issues = self.planner.validate_plan(invalid_plan)
        assert not is_valid
        assert "Missing required field: plan_id" in issues
        assert "Plan has no steps" in issues
    
    def test_estimate_duration(self):
        """Test duration estimation"""
        plan = {
            "steps": [
                {"timeout_ms": 300000},  # 5 minutes
                {"timeout_ms": 120000}   # 2 minutes
            ]
        }
        
        duration = self.planner._estimate_duration(plan)
        
        # Should be (5 + 2) * 1.2 = 8.4 minutes = 504000ms
        assert duration == 504000
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        agent_analysis = {
            "required_agents": ["content_writer", "social_media_publisher"],
            "workflow_pattern": "content_creation"
        }
        selected_agents = [
            {"id": "content_writer", "rationale": "Create content"},
            {"id": "social_media_publisher", "rationale": "Publish content"}
        ]
        
        confidence = self.planner._calculate_confidence(agent_analysis, selected_agents)
        
        # Should have high confidence
        assert confidence >= 0.8


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
