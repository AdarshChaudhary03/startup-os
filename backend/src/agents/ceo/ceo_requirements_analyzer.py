from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime, timezone
from src.services.ai_service import ai_service


class CEORequirementsAnalyzer:
    """Advanced requirements analysis and documentation generator for CEO agent"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analysis_templates = self._initialize_templates()
        self.requirement_patterns = self._initialize_patterns()
    
    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize analysis templates"""
        return {
            "functional_requirements": """
Based on the gathered information, identify and list the functional requirements:
1. Core functionality needed
2. User interactions required
3. System behaviors expected
4. Input/output specifications
5. Integration requirements
""",
            "non_functional_requirements": """
Identify non-functional requirements:
1. Performance expectations
2. Security requirements
3. Scalability needs
4. Usability standards
5. Compliance requirements
""",
            "technical_specifications": """
Define technical specifications:
1. Technology stack preferences
2. Architecture patterns
3. API requirements
4. Data storage needs
5. Third-party integrations
""",
            "project_scope": """
Define project scope:
1. In-scope features
2. Out-of-scope items
3. Assumptions
4. Dependencies
5. Risks and mitigation
"""
        }
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Initialize requirement detection patterns"""
        return {
            "functional": [
                "feature", "function", "capability", "ability", "should be able to",
                "must have", "need to", "require", "functionality"
            ],
            "performance": [
                "fast", "quick", "speed", "performance", "efficient", "optimize",
                "response time", "latency", "throughput"
            ],
            "security": [
                "secure", "security", "authentication", "authorization", "encrypt",
                "privacy", "protect", "safe", "compliance"
            ],
            "scalability": [
                "scale", "scalable", "growth", "expand", "handle load", "concurrent",
                "users", "volume", "capacity"
            ],
            "usability": [
                "user-friendly", "intuitive", "easy to use", "accessible", "UX",
                "UI", "interface", "experience"
            ]
        }
    
    async def analyze_requirements(self, 
                                 task: str, 
                                 responses: Dict[str, str], 
                                 context: Dict[str, Any],
                                 request_id: str) -> Dict[str, Any]:
        """Perform comprehensive requirements analysis"""
        
        # Combine all information
        full_context = self._compile_full_context(task, responses, context)
        
        # Analyze different aspects
        functional_reqs = await self._analyze_functional_requirements(full_context, request_id)
        non_functional_reqs = await self._analyze_non_functional_requirements(full_context, request_id)
        technical_specs = await self._analyze_technical_specifications(full_context, request_id)
        project_scope = await self._analyze_project_scope(full_context, request_id)
        
        # Detect requirement patterns
        detected_patterns = self._detect_requirement_patterns(full_context)
        
        # Generate comprehensive analysis
        analysis = {
            "functional_requirements": functional_reqs,
            "non_functional_requirements": non_functional_reqs,
            "technical_specifications": technical_specs,
            "project_scope": project_scope,
            "detected_patterns": detected_patterns,
            "priority_level": self._determine_priority(responses),
            "complexity_assessment": self._assess_complexity(functional_reqs, non_functional_reqs),
            "risk_assessment": self._assess_risks(full_context),
            "success_metrics": self._define_success_metrics(task, responses),
            "recommendations": self._generate_recommendations(detected_patterns)
        }
        
        return analysis
    
    def _compile_full_context(self, task: str, responses: Dict[str, str], context: Dict[str, Any]) -> str:
        """Compile all information into a comprehensive context"""
        
        parts = [f"Original Task: {task}"]
        
        # Add responses
        for question_id, response in responses.items():
            parts.append(f"{question_id}: {response}")
        
        # Add additional context
        if context.get("user_context"):
            parts.append(f"User Context: {json.dumps(context['user_context'])}")
        
        if context.get("similar_requirements"):
            parts.append(f"Similar Requirements Found: {len(context['similar_requirements'])}")
        
        return "\n\n".join(parts)
    
    async def _analyze_functional_requirements(self, context: str, request_id: str) -> List[Dict[str, Any]]:
        """Analyze and extract functional requirements"""
        
        prompt = f"""
Analyze the following context and extract functional requirements:

{context}

{self.analysis_templates['functional_requirements']}

Return a JSON array of functional requirements, each with:
{{
    "id": "FR-001",
    "description": "Clear description of the requirement",
    "priority": "high/medium/low",
    "category": "core/auxiliary/optional",
    "acceptance_criteria": ["List of criteria"]
}}
"""
        
        try:
            result = await ai_service.generate_content(prompt, request_id)
            requirements = json.loads(result)
            
            # Validate and enhance requirements
            return self._validate_functional_requirements(requirements)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze functional requirements: {e}")
            return self._generate_default_functional_requirements(context)
    
    async def _analyze_non_functional_requirements(self, context: str, request_id: str) -> List[Dict[str, Any]]:
        """Analyze and extract non-functional requirements"""
        
        prompt = f"""
Analyze the following context and extract non-functional requirements:

{context}

{self.analysis_templates['non_functional_requirements']}

Return a JSON array of non-functional requirements, each with:
{{
    "id": "NFR-001",
    "type": "performance/security/scalability/usability/reliability",
    "description": "Clear description",
    "metric": "Measurable metric",
    "target_value": "Target value or range"
}}
"""
        
        try:
            result = await ai_service.generate_content(prompt, request_id)
            requirements = json.loads(result)
            
            return self._validate_non_functional_requirements(requirements)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze non-functional requirements: {e}")
            return self._generate_default_non_functional_requirements(context)
    
    async def _analyze_technical_specifications(self, context: str, request_id: str) -> Dict[str, Any]:
        """Analyze and extract technical specifications"""
        
        prompt = f"""
Analyze the following context and define technical specifications:

{context}

{self.analysis_templates['technical_specifications']}

Return a JSON object with:
{{
    "technology_stack": {{
        "frontend": [],
        "backend": [],
        "database": [],
        "infrastructure": []
    }},
    "architecture_pattern": "Description of architecture",
    "api_specifications": [],
    "integration_points": [],
    "deployment_requirements": {{}}
}}
"""
        
        try:
            result = await ai_service.generate_content(prompt, request_id)
            specs = json.loads(result)
            
            return self._validate_technical_specifications(specs)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze technical specifications: {e}")
            return self._generate_default_technical_specifications()
    
    async def _analyze_project_scope(self, context: str, request_id: str) -> Dict[str, Any]:
        """Analyze and define project scope"""
        
        prompt = f"""
Analyze the following context and define project scope:

{context}

{self.analysis_templates['project_scope']}

Return a JSON object with:
{{
    "in_scope": ["List of in-scope items"],
    "out_of_scope": ["List of out-of-scope items"],
    "assumptions": ["List of assumptions"],
    "dependencies": ["List of dependencies"],
    "risks": [
        {{
            "description": "Risk description",
            "impact": "high/medium/low",
            "probability": "high/medium/low",
            "mitigation": "Mitigation strategy"
        }}
    ]
}}
"""
        
        try:
            result = await ai_service.generate_content(prompt, request_id)
            scope = json.loads(result)
            
            return self._validate_project_scope(scope)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze project scope: {e}")
            return self._generate_default_project_scope()
    
    def _detect_requirement_patterns(self, context: str) -> Dict[str, List[str]]:
        """Detect requirement patterns in the context"""
        
        detected = {}
        context_lower = context.lower()
        
        for pattern_type, keywords in self.requirement_patterns.items():
            found_keywords = []
            for keyword in keywords:
                if keyword in context_lower:
                    found_keywords.append(keyword)
            
            if found_keywords:
                detected[pattern_type] = found_keywords
        
        return detected
    
    def _determine_priority(self, responses: Dict[str, str]) -> str:
        """Determine overall priority based on responses"""
        
        priority_indicators = {
            "urgent": ["urgent", "asap", "immediately", "critical"],
            "high": ["important", "priority", "soon", "quickly"],
            "medium": ["normal", "standard", "regular"],
            "low": ["whenever", "no rush", "flexible", "optional"]
        }
        
        combined_text = " ".join(responses.values()).lower()
        
        for priority, indicators in priority_indicators.items():
            if any(indicator in combined_text for indicator in indicators):
                return priority
        
        return "medium"
    
    def _assess_complexity(self, functional_reqs: List[Dict], non_functional_reqs: List[Dict]) -> Dict[str, Any]:
        """Assess project complexity"""
        
        complexity_score = 0
        factors = []
        
        # Functional complexity
        func_count = len(functional_reqs)
        if func_count > 10:
            complexity_score += 3
            factors.append("High number of functional requirements")
        elif func_count > 5:
            complexity_score += 2
            factors.append("Moderate number of functional requirements")
        else:
            complexity_score += 1
            factors.append("Low number of functional requirements")
        
        # Non-functional complexity
        nf_count = len(non_functional_reqs)
        if nf_count > 5:
            complexity_score += 2
            factors.append("Multiple non-functional requirements")
        
        # Determine overall complexity
        if complexity_score >= 4:
            level = "high"
        elif complexity_score >= 2:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "score": complexity_score,
            "factors": factors
        }
    
    def _assess_risks(self, context: str) -> List[Dict[str, str]]:
        """Assess potential risks"""
        
        risks = []
        context_lower = context.lower()
        
        # Technical risks
        if "new technology" in context_lower or "unfamiliar" in context_lower:
            risks.append({
                "type": "technical",
                "description": "Use of new or unfamiliar technology",
                "impact": "medium",
                "mitigation": "Allocate time for learning and prototyping"
            })
        
        # Timeline risks
        if "urgent" in context_lower or "asap" in context_lower:
            risks.append({
                "type": "timeline",
                "description": "Tight timeline constraints",
                "impact": "high",
                "mitigation": "Prioritize core features and consider phased delivery"
            })
        
        # Integration risks
        if "integrate" in context_lower or "third-party" in context_lower:
            risks.append({
                "type": "integration",
                "description": "Third-party integration dependencies",
                "impact": "medium",
                "mitigation": "Early API testing and fallback strategies"
            })
        
        return risks
    
    def _define_success_metrics(self, task: str, responses: Dict[str, str]) -> List[Dict[str, str]]:
        """Define success metrics for the project"""
        
        metrics = []
        
        # Always include completion metric
        metrics.append({
            "metric": "Project Completion",
            "target": "100% of defined requirements implemented",
            "measurement": "Requirement traceability matrix"
        })
        
        # Add specific metrics based on context
        combined_text = f"{task} {' '.join(responses.values())}".lower()
        
        if "performance" in combined_text:
            metrics.append({
                "metric": "System Performance",
                "target": "Response time < 2 seconds for 95% of requests",
                "measurement": "Performance monitoring tools"
            })
        
        if "user" in combined_text or "customer" in combined_text:
            metrics.append({
                "metric": "User Satisfaction",
                "target": "User satisfaction score >= 4.0/5.0",
                "measurement": "User surveys and feedback"
            })
        
        if "quality" in combined_text:
            metrics.append({
                "metric": "Code Quality",
                "target": "Code coverage >= 80%, 0 critical bugs",
                "measurement": "Static analysis and testing tools"
            })
        
        return metrics
    
    def _generate_recommendations(self, detected_patterns: Dict[str, List[str]]) -> List[str]:
        """Generate recommendations based on detected patterns"""
        
        recommendations = []
        
        if "performance" in detected_patterns:
            recommendations.append("Consider implementing caching strategies and performance monitoring from the start")
        
        if "security" in detected_patterns:
            recommendations.append("Implement security best practices including authentication, authorization, and data encryption")
        
        if "scalability" in detected_patterns:
            recommendations.append("Design with horizontal scalability in mind using microservices or serverless architecture")
        
        if "usability" in detected_patterns:
            recommendations.append("Conduct user research and usability testing throughout the development process")
        
        # Always add general recommendations
        recommendations.extend([
            "Establish clear communication channels with stakeholders",
            "Set up continuous integration and deployment pipelines",
            "Document architectural decisions and API specifications"
        ])
        
        return recommendations
    
    # Validation methods
    def _validate_functional_requirements(self, requirements: List[Dict]) -> List[Dict[str, Any]]:
        """Validate and enhance functional requirements"""
        
        validated = []
        for i, req in enumerate(requirements):
            # Ensure required fields
            validated_req = {
                "id": req.get("id", f"FR-{i+1:03d}"),
                "description": req.get("description", "Requirement description"),
                "priority": req.get("priority", "medium"),
                "category": req.get("category", "core"),
                "acceptance_criteria": req.get("acceptance_criteria", [])
            }
            
            # Ensure at least one acceptance criterion
            if not validated_req["acceptance_criteria"]:
                validated_req["acceptance_criteria"] = [
                    f"The system successfully {validated_req['description'].lower()}"
                ]
            
            validated.append(validated_req)
        
        return validated
    
    def _validate_non_functional_requirements(self, requirements: List[Dict]) -> List[Dict[str, Any]]:
        """Validate and enhance non-functional requirements"""
        
        validated = []
        for i, req in enumerate(requirements):
            validated_req = {
                "id": req.get("id", f"NFR-{i+1:03d}"),
                "type": req.get("type", "performance"),
                "description": req.get("description", "Requirement description"),
                "metric": req.get("metric", "To be defined"),
                "target_value": req.get("target_value", "To be determined")
            }
            validated.append(validated_req)
        
        return validated
    
    def _validate_technical_specifications(self, specs: Dict) -> Dict[str, Any]:
        """Validate and enhance technical specifications"""
        
        default_stack = {
            "frontend": [],
            "backend": [],
            "database": [],
            "infrastructure": []
        }
        
        return {
            "technology_stack": specs.get("technology_stack", default_stack),
            "architecture_pattern": specs.get("architecture_pattern", "To be determined"),
            "api_specifications": specs.get("api_specifications", []),
            "integration_points": specs.get("integration_points", []),
            "deployment_requirements": specs.get("deployment_requirements", {})
        }
    
    def _validate_project_scope(self, scope: Dict) -> Dict[str, Any]:
        """Validate and enhance project scope"""
        
        return {
            "in_scope": scope.get("in_scope", ["Core functionality as defined in requirements"]),
            "out_of_scope": scope.get("out_of_scope", []),
            "assumptions": scope.get("assumptions", []),
            "dependencies": scope.get("dependencies", []),
            "risks": scope.get("risks", [])
        }
    
    # Default generation methods (fallbacks)
    def _generate_default_functional_requirements(self, context: str) -> List[Dict[str, Any]]:
        """Generate default functional requirements as fallback"""
        
        return [
            {
                "id": "FR-001",
                "description": "Implement core functionality as described in the task",
                "priority": "high",
                "category": "core",
                "acceptance_criteria": [
                    "The system performs the requested task successfully",
                    "All user inputs are validated",
                    "Appropriate feedback is provided to users"
                ]
            }
        ]
    
    def _generate_default_non_functional_requirements(self, context: str) -> List[Dict[str, Any]]:
        """Generate default non-functional requirements as fallback"""
        
        return [
            {
                "id": "NFR-001",
                "type": "performance",
                "description": "System response time",
                "metric": "Average response time",
                "target_value": "< 3 seconds"
            },
            {
                "id": "NFR-002",
                "type": "reliability",
                "description": "System availability",
                "metric": "Uptime percentage",
                "target_value": ">= 99%"
            }
        ]
    
    def _generate_default_technical_specifications(self) -> Dict[str, Any]:
        """Generate default technical specifications as fallback"""
        
        return {
            "technology_stack": {
                "frontend": ["To be determined based on requirements"],
                "backend": ["To be determined based on requirements"],
                "database": ["To be determined based on data needs"],
                "infrastructure": ["Cloud-based solution recommended"]
            },
            "architecture_pattern": "Modular architecture with clear separation of concerns",
            "api_specifications": ["RESTful API design principles"],
            "integration_points": ["To be identified based on requirements"],
            "deployment_requirements": {
                "environment": "Development, staging, and production",
                "ci_cd": "Automated deployment pipeline recommended"
            }
        }
    
    def _generate_default_project_scope(self) -> Dict[str, Any]:
        """Generate default project scope as fallback"""
        
        return {
            "in_scope": [
                "Core functionality implementation",
                "Basic user interface",
                "Essential integrations",
                "Documentation"
            ],
            "out_of_scope": [
                "Features not explicitly requested",
                "Third-party system modifications",
                "Infrastructure provisioning (unless specified)"
            ],
            "assumptions": [
                "Required resources will be available",
                "Stakeholders will provide timely feedback",
                "No major requirement changes after approval"
            ],
            "dependencies": [
                "Access to necessary systems and APIs",
                "Availability of required tools and licenses"
            ],
            "risks": [
                {
                    "description": "Requirement changes during development",
                    "impact": "medium",
                    "probability": "medium",
                    "mitigation": "Regular stakeholder communication and sign-offs"
                }
            ]
        }
    
    def generate_documentation(self, analysis: Dict[str, Any], format: str = "markdown") -> str:
        """Generate comprehensive requirements documentation"""
        
        if format == "markdown":
            return self._generate_markdown_documentation(analysis)
        elif format == "json":
            return json.dumps(analysis, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_markdown_documentation(self, analysis: Dict[str, Any]) -> str:
        """Generate markdown documentation from analysis"""
        
        doc = ["# Requirements Documentation\n"]
        doc.append(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
        
        # Executive Summary
        doc.append("## Executive Summary\n")
        doc.append(f"Priority Level: **{analysis['priority_level'].upper()}**\n")
        doc.append(f"Complexity: **{analysis['complexity_assessment']['level'].upper()}**\n")
        doc.append("\n")
        
        # Functional Requirements
        doc.append("## Functional Requirements\n")
        for req in analysis['functional_requirements']:
            doc.append(f"### {req['id']}: {req['description']}\n")
            doc.append(f"- Priority: {req['priority']}\n")
            doc.append(f"- Category: {req['category']}\n")
            doc.append("- Acceptance Criteria:\n")
            for criterion in req['acceptance_criteria']:
                doc.append(f"  - {criterion}\n")
            doc.append("\n")
        
        # Non-Functional Requirements
        doc.append("## Non-Functional Requirements\n")
        for req in analysis['non_functional_requirements']:
            doc.append(f"### {req['id']}: {req['description']}\n")
            doc.append(f"- Type: {req['type']}\n")
            doc.append(f"- Metric: {req['metric']}\n")
            doc.append(f"- Target: {req['target_value']}\n")
            doc.append("\n")
        
        # Technical Specifications
        doc.append("## Technical Specifications\n")
        tech_specs = analysis['technical_specifications']
        doc.append(f"### Architecture Pattern\n{tech_specs['architecture_pattern']}\n\n")
        
        doc.append("### Technology Stack\n")
        for category, technologies in tech_specs['technology_stack'].items():
            if technologies:
                doc.append(f"- **{category.capitalize()}**: {', '.join(technologies)}\n")
        doc.append("\n")
        
        # Project Scope
        doc.append("## Project Scope\n")
        scope = analysis['project_scope']
        
        doc.append("### In Scope\n")
        for item in scope['in_scope']:
            doc.append(f"- {item}\n")
        doc.append("\n")
        
        doc.append("### Out of Scope\n")
        for item in scope['out_of_scope']:
            doc.append(f"- {item}\n")
        doc.append("\n")
        
        # Risks
        if scope['risks']:
            doc.append("### Risks\n")
            for risk in scope['risks']:
                doc.append(f"- **{risk['description']}**\n")
                doc.append(f"  - Impact: {risk['impact']}\n")
                doc.append(f"  - Probability: {risk['probability']}\n")
                doc.append(f"  - Mitigation: {risk['mitigation']}\n")
            doc.append("\n")
        
        # Success Metrics
        doc.append("## Success Metrics\n")
        for metric in analysis['success_metrics']:
            doc.append(f"- **{metric['metric']}**\n")
            doc.append(f"  - Target: {metric['target']}\n")
            doc.append(f"  - Measurement: {metric['measurement']}\n")
        doc.append("\n")
        
        # Recommendations
        doc.append("## Recommendations\n")
        for recommendation in analysis['recommendations']:
            doc.append(f"- {recommendation}\n")
        
        return "".join(doc)


# Create global instance
ceo_requirements_analyzer = CEORequirementsAnalyzer()
