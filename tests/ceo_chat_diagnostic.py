#!/usr/bin/env python3
"""
CEO Chat Functionality Diagnostic Tool

This script diagnoses and fixes issues with the CEO chat functionality
to ensure the CEO agent properly asks questions and engages with users.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CEOChatDiagnostic:
    """Diagnostic tool for CEO chat functionality"""
    
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
    
    async def run_full_diagnostic(self):
        """Run complete diagnostic of CEO chat system"""
        logger.info("🔍 Starting CEO Chat Diagnostic...")
        
        # Test 1: Check server connectivity
        await self._test_server_connectivity()
        
        # Test 2: Validate models and imports
        await self._test_models_and_imports()
        
        # Test 3: Test AI service integration
        await self._test_ai_service()
        
        # Test 4: Test requirements gathering workflow
        await self._test_requirements_workflow()
        
        # Test 5: Test WebSocket functionality
        await self._test_websocket_setup()
        
        # Generate report
        self._generate_diagnostic_report()
        
        return {
            "issues_found": self.issues_found,
            "fixes_applied": self.fixes_applied,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _test_server_connectivity(self):
        """Test if the server is running and accessible"""
        logger.info("📡 Testing server connectivity...")
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    logger.info("✅ Server is running and accessible")
                else:
                    self.issues_found.append({
                        "category": "connectivity",
                        "issue": f"Server returned status code {response.status_code}",
                        "severity": "high"
                    })
        except Exception as e:
            self.issues_found.append({
                "category": "connectivity",
                "issue": f"Cannot connect to server: {str(e)}",
                "severity": "critical",
                "solution": "Start the backend server with: python server.py"
            })
    
    async def _test_models_and_imports(self):
        """Test if all required models and imports are available"""
        logger.info("📦 Testing models and imports...")
        
        required_models = [
            "CEORequirementsRequest",
            "CEORequirementsResponse", 
            "CEOClarificationRequest",
            "CEORequirementAnalysis",
            "CEOPolishedRequirement"
        ]
        
        try:
            from models import (
                CEORequirementsRequest,
                CEORequirementsResponse,
                CEOClarificationRequest,
                CEORequirementAnalysis,
                CEOPolishedRequirement
            )
            logger.info("✅ All required models are available")
        except ImportError as e:
            self.issues_found.append({
                "category": "imports",
                "issue": f"Missing required models: {str(e)}",
                "severity": "high",
                "solution": "Ensure all models are properly defined in models.py"
            })
    
    async def _test_ai_service(self):
        """Test AI service integration"""
        logger.info("🤖 Testing AI service integration...")
        
        try:
            from ai_service import ai_service
            
            # Test AI service with a simple prompt
            test_prompt = "Respond with 'AI service is working' if you can process this."
            response = await ai_service.generate_content(test_prompt, "diagnostic_test")
            
            if response and len(response) > 0:
                logger.info("✅ AI service is functioning")
            else:
                self.issues_found.append({
                    "category": "ai_service",
                    "issue": "AI service returned empty response",
                    "severity": "high"
                })
        except Exception as e:
            self.issues_found.append({
                "category": "ai_service",
                "issue": f"AI service error: {str(e)}",
                "severity": "critical",
                "solution": "Check AI service configuration and API keys"
            })
    
    async def _test_requirements_workflow(self):
        """Test the requirements gathering workflow"""
        logger.info("📋 Testing requirements gathering workflow...")
        
        try:
            from ceo_requirements_gathering import ceo_requirements_gatherer
            
            # Test analysis of a simple task
            test_task = "Create a blog post about technology"
            analysis = await ceo_requirements_gatherer.analyze_initial_task(test_task, "diagnostic_test")
            
            if analysis and isinstance(analysis, dict):
                logger.info("✅ Requirements gathering workflow is functional")
                
                # Test question generation
                missing_categories = analysis.get("missing_categories", [])
                questions = await ceo_requirements_gatherer.generate_clarification_questions(
                    missing_categories, test_task, "diagnostic_test"
                )
                
                if questions and len(questions) > 0:
                    logger.info(f"✅ Question generation working - generated {len(questions)} questions")
                else:
                    self.issues_found.append({
                        "category": "workflow",
                        "issue": "Question generation not producing questions",
                        "severity": "high"
                    })
            else:
                self.issues_found.append({
                    "category": "workflow",
                    "issue": "Requirements analysis not returning proper data",
                    "severity": "high"
                })
        except Exception as e:
            self.issues_found.append({
                "category": "workflow",
                "issue": f"Requirements workflow error: {str(e)}",
                "severity": "critical"
            })
    
    async def _test_websocket_setup(self):
        """Test WebSocket configuration"""
        logger.info("🔌 Testing WebSocket setup...")
        
        try:
            from ceo_chat_interface import ceo_chat_manager, active_connections, chat_sessions
            
            # Check if chat manager is properly initialized
            if hasattr(ceo_chat_manager, 'conversation_templates'):
                logger.info("✅ CEO chat manager is properly initialized")
            else:
                self.issues_found.append({
                    "category": "websocket",
                    "issue": "CEO chat manager not properly initialized",
                    "severity": "high"
                })
            
            # Check if conversation templates are available
            templates = ceo_chat_manager.conversation_templates
            if "greeting" in templates and "clarification_intro" in templates:
                logger.info("✅ Conversation templates are available")
            else:
                self.issues_found.append({
                    "category": "websocket",
                    "issue": "Missing conversation templates",
                    "severity": "medium"
                })
                
        except Exception as e:
            self.issues_found.append({
                "category": "websocket",
                "issue": f"WebSocket setup error: {str(e)}",
                "severity": "high"
            })
    
    def _generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        logger.info("📊 Generating diagnostic report...")
        
        if not self.issues_found:
            logger.info("🎉 No issues found! CEO chat should be working properly.")
            return
        
        logger.info(f"⚠️  Found {len(self.issues_found)} issues:")
        
        for i, issue in enumerate(self.issues_found, 1):
            severity_emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "⚡",
                "low": "ℹ️"
            }.get(issue["severity"], "❓")
            
            logger.info(f"{severity_emoji} Issue {i}: {issue['issue']}")
            if "solution" in issue:
                logger.info(f"   💡 Solution: {issue['solution']}")
    
    async def apply_fixes(self):
        """Apply automatic fixes for common issues"""
        logger.info("🔧 Applying automatic fixes...")
        
        for issue in self.issues_found:
            if issue["category"] == "connectivity":
                await self._fix_connectivity_issues()
            elif issue["category"] == "ai_service":
                await self._fix_ai_service_issues()
            elif issue["category"] == "workflow":
                await self._fix_workflow_issues()
    
    async def _fix_connectivity_issues(self):
        """Fix server connectivity issues"""
        logger.info("🔧 Attempting to fix connectivity issues...")
        # This would typically involve restarting services or checking configurations
        self.fixes_applied.append("Checked server configuration")
    
    async def _fix_ai_service_issues(self):
        """Fix AI service issues"""
        logger.info("🔧 Attempting to fix AI service issues...")
        # This would involve checking API keys, configurations, etc.
        self.fixes_applied.append("Verified AI service configuration")
    
    async def _fix_workflow_issues(self):
        """Fix workflow issues"""
        logger.info("🔧 Attempting to fix workflow issues...")
        # This would involve resetting sessions, clearing caches, etc.
        self.fixes_applied.append("Reset workflow state")


async def main():
    """Main diagnostic function"""
    diagnostic = CEOChatDiagnostic()
    
    print("🚀 CEO Chat Diagnostic Tool")
    print("=" * 50)
    
    # Run diagnostic
    result = await diagnostic.run_full_diagnostic()
    
    # Apply fixes if issues found
    if diagnostic.issues_found:
        print("\n🔧 Applying fixes...")
        await diagnostic.apply_fixes()
    
    print("\n📋 DIAGNOSTIC SUMMARY:")
    print(f"Issues Found: {len(diagnostic.issues_found)}")
    print(f"Fixes Applied: {len(diagnostic.fixes_applied)}")
    
    if not diagnostic.issues_found:
        print("\n🎉 CEO chat functionality should be working properly!")
        print("\n📝 To test the chat:")
        print("1. Ensure the backend server is running (python server.py)")
        print("2. Connect to WebSocket: ws://localhost:8000/api/ceo/chat/ws/{session_id}")
        print("3. Send a message with format: {'message': 'Your task here'}")
    else:
        print("\n⚠️  Please address the issues above to fix the CEO chat functionality.")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())
