"""Technical Writing Agent

Specialized agent for generating technical documentation, API docs,
user guides, tutorials, and other technical content.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone

from .base import BaseContentAgent
from ..config import (
    ContentWriterV2Config, 
    ContentFormat, 
    ToneStyle,
    DEFAULT_CONFIG
)
from ....core.ai_providers.exceptions import AIProviderError
from ....core.logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class TechnicalWritingAgent(BaseContentAgent):
    """Specialized agent for technical writing and documentation."""
    
    def __init__(self, config: Optional[ContentWriterV2Config] = None):
        """Initialize the Technical Writing Agent.
        
        Args:
            config: Configuration for the agent
        """
        super().__init__(config)
        self.technical_config = self.config.technical
    
    async def generate_content(
        self,
        task: str,
        request_id: str,
        doc_type: str = "user_guide",
        technical_level: Optional[str] = None,
        include_code_examples: Optional[bool] = None,
        programming_language: Optional[str] = None,
        target_audience: Optional[str] = None,
        product_name: Optional[str] = None,
        api_endpoints: Optional[List[str]] = None,
        code_snippets: Optional[List[str]] = None,
        tone: Optional[ToneStyle] = None,
        brand_context: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate technical documentation content.
        
        Args:
            task: Documentation topic or description
            request_id: Unique request identifier
            doc_type: Type of documentation (api_docs, user_guide, tutorial, etc.)
            technical_level: Technical level (beginner, intermediate, advanced)
            include_code_examples: Whether to include code examples
            programming_language: Programming language for code examples
            target_audience: Target audience description
            product_name: Name of the product/service being documented
            api_endpoints: List of API endpoints to document
            code_snippets: List of code snippets to include
            tone: Tone and style
            brand_context: Brand context and guidelines
            additional_instructions: Additional instructions
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with generated content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Use defaults from config
        technical_level = technical_level or self.technical_config.target_audience_level
        include_code_examples = include_code_examples if include_code_examples is not None else self.technical_config.include_code_examples
        
        # Log generation start
        log_orchestration_event(
            request_id=request_id,
            event_type="technical_writing_generation_start",
            agent_id="technical_writing_agent",
            message="Starting technical documentation generation",
            additional_data={
                "doc_type": doc_type,
                "technical_level": technical_level,
                "include_code_examples": include_code_examples,
                "programming_language": programming_language
            }
        )
        
        try:
            # Build technical documentation prompt
            prompt = self._build_technical_prompt(
                task=task,
                doc_type=doc_type,
                technical_level=technical_level,
                include_code_examples=include_code_examples,
                programming_language=programming_language,
                target_audience=target_audience,
                product_name=product_name,
                api_endpoints=api_endpoints,
                code_snippets=code_snippets,
                tone=tone,
                brand_context=brand_context,
                additional_instructions=additional_instructions
            )
            
            # Generate technical content
            response = await self._generate_with_provider(
                prompt=prompt,
                request_id=request_id,
                temperature=0.3,  # Lower creativity for technical accuracy
                max_tokens=3000  # Technical docs can be longer
            )
            
            content = response.content.strip()
            
            # Post-process technical content
            processed_content = await self._post_process_technical_content(
                content=content,
                doc_type=doc_type,
                include_code_examples=include_code_examples,
                programming_language=programming_language,
                request_id=request_id
            )
            
            # Analyze technical content
            tech_analysis = await self._analyze_technical_content(
                content=processed_content,
                doc_type=doc_type,
                technical_level=technical_level,
                include_code_examples=include_code_examples
            )
            
            # Build metadata
            metadata = self._extract_content_metadata(
                content=processed_content,
                doc_type=doc_type,
                technical_level=technical_level,
                programming_language=programming_language,
                code_block_count=tech_analysis["code_block_count"],
                section_count=tech_analysis["section_count"],
                complexity_score=tech_analysis["complexity_score"],
                completeness_score=tech_analysis["completeness_score"],
                tone_used=tone.value if tone else "technical"
            )
            
            result = {
                "content": processed_content,
                "metadata": metadata,
                "technical_analysis": tech_analysis,
                "suggestions": await self._get_technical_suggestions(doc_type, tech_analysis)
            }
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="technical_writing_generation_complete",
                agent_id="technical_writing_agent",
                message="Technical documentation generated successfully",
                additional_data={
                    "doc_type": doc_type,
                    "content_length": len(processed_content),
                    "code_block_count": tech_analysis["code_block_count"],
                    "complexity_score": tech_analysis["complexity_score"]
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="technical_writing_generation_error",
                agent_id="technical_writing_agent",
                message=f"Technical documentation generation failed: {str(e)}",
                additional_data={
                    "doc_type": doc_type,
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Technical documentation generation failed for request {request_id}: {e}")
            raise AIProviderError(f"Technical documentation generation failed: {str(e)}")
    
    def _build_technical_prompt(
        self,
        task: str,
        doc_type: str,
        technical_level: str,
        include_code_examples: bool,
        programming_language: Optional[str],
        target_audience: Optional[str],
        product_name: Optional[str],
        api_endpoints: Optional[List[str]],
        code_snippets: Optional[List[str]],
        tone: Optional[ToneStyle],
        brand_context: Optional[str],
        additional_instructions: Optional[str]
    ) -> str:
        """Build a technical documentation specific prompt.
        
        Returns:
            Complete prompt string
        """
        # Documentation type specific prompts
        doc_type_prompts = {
            "api_docs": """
Create comprehensive API documentation that:
- Provides clear endpoint descriptions and parameters
- Includes request/response examples with proper formatting
- Documents authentication and authorization requirements
- Explains error codes and troubleshooting
- Uses consistent formatting and structure
- Includes code examples in multiple programming languages
- Provides integration guides and best practices
""",
            "user_guide": """
Create a user-friendly guide that:
- Uses clear, step-by-step instructions
- Includes screenshots or visual aids descriptions
- Anticipates common user questions and issues
- Provides troubleshooting sections
- Uses consistent terminology throughout
- Organizes information logically from basic to advanced
- Includes practical examples and use cases
""",
            "tutorial": """
Create an educational tutorial that:
- Breaks down complex concepts into digestible steps
- Builds knowledge progressively from basics to advanced
- Includes hands-on exercises and examples
- Provides clear learning objectives
- Uses practical, real-world scenarios
- Includes code examples with explanations
- Offers additional resources for further learning
""",
            "installation_guide": """
Create a comprehensive installation guide that:
- Lists all system requirements and prerequisites
- Provides step-by-step installation instructions
- Covers multiple operating systems/environments
- Includes troubleshooting for common issues
- Provides verification steps to confirm successful installation
- Includes uninstallation instructions
- Offers alternative installation methods
""",
            "troubleshooting_guide": """
Create a helpful troubleshooting guide that:
- Organizes issues by category and severity
- Provides clear problem descriptions and symptoms
- Offers step-by-step solution procedures
- Includes diagnostic commands and tools
- Provides multiple solution approaches when possible
- Includes prevention tips and best practices
- Offers escalation paths for unresolved issues
""",
            "reference_manual": """
Create a comprehensive reference manual that:
- Organizes information alphabetically or by category
- Provides complete parameter and option descriptions
- Includes syntax examples and usage patterns
- Uses consistent formatting and structure
- Provides cross-references between related topics
- Includes quick reference sections
- Offers comprehensive coverage of all features
"""
        }
        
        system_prompt = doc_type_prompts.get(doc_type, doc_type_prompts["user_guide"])
        
        # Technical level adjustments
        level_adjustments = {
            "beginner": "Use simple language, explain technical terms, provide more context and background information.",
            "intermediate": "Assume basic technical knowledge, focus on practical implementation and best practices.",
            "advanced": "Use technical terminology freely, focus on complex scenarios and edge cases."
        }
        
        if technical_level in level_adjustments:
            system_prompt += f"\n\nTechnical Level: {level_adjustments[technical_level]}"
        
        # Code examples instruction
        if include_code_examples:
            system_prompt += "\n- Include relevant, well-commented code examples"
            if programming_language:
                system_prompt += f" in {programming_language}"
        
        # Tone instructions
        tone_instructions = ""
        if tone:
            tone_map = {
                ToneStyle.PROFESSIONAL: "Maintain a professional, authoritative tone.",
                ToneStyle.FRIENDLY: "Use a helpful, approachable tone.",
                ToneStyle.EDUCATIONAL: "Focus on teaching and explaining concepts clearly.",
                ToneStyle.CONVERSATIONAL: "Write in a conversational, easy-to-follow style.",
                ToneStyle.TECHNICAL: "Use precise technical language appropriate for the audience."
            }
            tone_instructions = tone_map.get(tone, "")
        
        # Build requirements
        requirements = []
        requirements.append(f"Topic: {task}")
        requirements.append(f"Documentation type: {doc_type}")
        requirements.append(f"Technical level: {technical_level}")
        
        if product_name:
            requirements.append(f"Product/Service: {product_name}")
        
        if target_audience:
            requirements.append(f"Target audience: {target_audience}")
        
        if programming_language:
            requirements.append(f"Programming language: {programming_language}")
        
        if api_endpoints:
            requirements.append(f"API endpoints to document: {', '.join(api_endpoints)}")
        
        if code_snippets:
            requirements.append(f"Include these code examples: {', '.join(code_snippets[:3])}...")  # Limit preview
        
        if tone_instructions:
            requirements.append(f"Tone: {tone_instructions}")
        
        if brand_context:
            requirements.append(f"Brand context: {brand_context}")
        
        if additional_instructions:
            requirements.append(f"Additional instructions: {additional_instructions}")
        
        # Documentation format
        requirements.append(f"Format: {self.technical_config.documentation_style}")
        
        # Combine all parts
        prompt_parts = [system_prompt]
        prompt_parts.append("\nSpecific requirements:")
        prompt_parts.extend([f"- {req}" for req in requirements])
        
        prompt_parts.append(
            "\nCreate clear, accurate, and comprehensive technical documentation that serves "
            "the target audience effectively. Focus on usability and practical value."
        )
        
        return "\n".join(prompt_parts)
    
    async def _post_process_technical_content(
        self,
        content: str,
        doc_type: str,
        include_code_examples: bool,
        programming_language: Optional[str],
        request_id: str
    ) -> str:
        """Post-process technical content for optimization.
        
        Args:
            content: Generated technical content
            doc_type: Type of documentation
            include_code_examples: Whether code examples should be included
            programming_language: Programming language for code examples
            request_id: Request identifier
        
        Returns:
            Post-processed content
        """
        processed_content = content
        
        # Ensure proper code block formatting
        if include_code_examples:
            processed_content = self._format_code_blocks(
                processed_content, 
                programming_language
            )
        
        # Add proper markdown formatting
        processed_content = self._format_technical_markdown(processed_content)
        
        # Ensure consistent terminology
        processed_content = self._standardize_terminology(processed_content)
        
        return processed_content.strip()
    
    def _format_code_blocks(self, content: str, language: Optional[str]) -> str:
        """Format code blocks with proper syntax highlighting.
        
        Args:
            content: Content with code blocks
            language: Programming language
        
        Returns:
            Content with properly formatted code blocks
        """
        import re
        
        # Find code blocks that aren't properly formatted
        # Simple pattern - could be enhanced
        if language:
            # Ensure code blocks have language specification
            content = re.sub(
                r'```\n((?:(?!```).)*)```',
                f'```{language}\n\\1```',
                content,
                flags=re.DOTALL
            )
        
        return content
    
    def _format_technical_markdown(self, content: str) -> str:
        """Format content with proper technical markdown.
        
        Args:
            content: Content to format
        
        Returns:
            Formatted content
        """
        import re
        
        # Ensure proper heading hierarchy
        content = re.sub(r'^(#{4,}) ', r'### ', content, flags=re.MULTILINE)
        
        # Format API endpoints
        content = re.sub(
            r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)',
            r'`\1 \2`',
            content
        )
        
        # Format inline code for technical terms
        tech_terms = ['API', 'JSON', 'HTTP', 'URL', 'SQL', 'XML', 'CSV']
        for term in tech_terms:
            content = re.sub(
                f'\b({term})\b(?!`)',
                r'`\1`',
                content
            )
        
        return content
    
    def _standardize_terminology(self, content: str) -> str:
        """Standardize technical terminology for consistency.
        
        Args:
            content: Content to standardize
        
        Returns:
            Content with standardized terminology
        """
        # Common technical term standardizations
        standardizations = {
            'api key': 'API key',
            'json': 'JSON',
            'http': 'HTTP',
            'https': 'HTTPS',
            'url': 'URL',
            'sql': 'SQL',
            'xml': 'XML',
            'csv': 'CSV'
        }
        
        for old_term, new_term in standardizations.items():
            content = content.replace(old_term, new_term)
        
        return content
    
    async def _analyze_technical_content(
        self,
        content: str,
        doc_type: str,
        technical_level: str,
        include_code_examples: bool
    ) -> Dict[str, Any]:
        """Analyze technical content for quality metrics.
        
        Args:
            content: Technical content
            doc_type: Type of documentation
            technical_level: Technical level
            include_code_examples: Whether code examples should be included
        
        Returns:
            Analysis results
        """
        import re
        
        word_count = len(content.split())
        char_count = len(content)
        
        # Count structural elements
        h1_count = len(re.findall(r'^# .+', content, re.MULTILINE))
        h2_count = len(re.findall(r'^## .+', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### .+', content, re.MULTILINE))
        section_count = h1_count + h2_count + h3_count
        
        # Count code blocks
        code_block_count = len(re.findall(r'```[\s\S]*?```', content))
        inline_code_count = len(re.findall(r'`[^`]+`', content))
        
        # Count technical elements
        api_endpoint_count = len(re.findall(r'(GET|POST|PUT|DELETE|PATCH)\s+/', content))
        parameter_count = len(re.findall(r'\*\*[Pp]arameter[s]?\*\*|\*\*[Aa]rg[s]?\*\*', content))
        example_count = len(re.findall(r'[Ee]xample|[Ss]ample', content))
        
        # Calculate complexity score
        complexity_indicators = {
            'technical_terms': len(re.findall(r'\b(API|HTTP|JSON|XML|SQL|database|server|client|endpoint)\b', content, re.IGNORECASE)),
            'code_blocks': code_block_count,
            'parameters': parameter_count,
            'nested_lists': len(re.findall(r'^\s+[-*+]', content, re.MULTILINE))
        }
        
        complexity_score = min(100, sum(complexity_indicators.values()) * 5)
        
        # Calculate completeness score
        completeness_factors = {
            'has_introduction': bool(re.search(r'introduction|overview|getting started', content, re.IGNORECASE)),
            'has_examples': example_count > 0,
            'has_code_blocks': code_block_count > 0 if include_code_examples else True,
            'has_proper_structure': section_count >= 3,
            'has_troubleshooting': bool(re.search(r'troubleshoot|error|problem|issue', content, re.IGNORECASE))
        }
        
        completeness_score = (sum(completeness_factors.values()) / len(completeness_factors)) * 100
        
        # Technical accuracy indicators
        accuracy_indicators = {
            'consistent_terminology': self._check_terminology_consistency(content),
            'proper_formatting': bool(re.search(r'```\w+', content)),  # Code blocks with language
            'clear_structure': section_count > 0
        }
        
        accuracy_score = (sum(accuracy_indicators.values()) / len(accuracy_indicators)) * 100
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "section_count": section_count,
            "heading_counts": {
                "h1": h1_count,
                "h2": h2_count,
                "h3": h3_count
            },
            "code_block_count": code_block_count,
            "inline_code_count": inline_code_count,
            "api_endpoint_count": api_endpoint_count,
            "parameter_count": parameter_count,
            "example_count": example_count,
            "complexity_score": round(complexity_score, 1),
            "completeness_score": round(completeness_score, 1),
            "accuracy_score": round(accuracy_score, 1),
            "technical_level": technical_level,
            "doc_type": doc_type,
            "estimated_reading_time_minutes": max(1, round(word_count / 200)),
            "complexity_indicators": complexity_indicators,
            "completeness_factors": completeness_factors
        }
    
    def _check_terminology_consistency(self, content: str) -> bool:
        """Check if technical terminology is used consistently.
        
        Args:
            content: Content to check
        
        Returns:
            True if terminology is consistent
        """
        import re
        
        # Simple consistency check for common terms
        inconsistencies = [
            (r'\bapi\b', r'\bAPI\b'),  # Should be uppercase
            (r'\bjson\b', r'\bJSON\b'),  # Should be uppercase
            (r'\bhttp\b', r'\bHTTP\b'),  # Should be uppercase
        ]
        
        for lowercase_pattern, uppercase_pattern in inconsistencies:
            lowercase_count = len(re.findall(lowercase_pattern, content, re.IGNORECASE))
            uppercase_count = len(re.findall(uppercase_pattern, content))
            
            # If both forms exist, it's inconsistent
            if lowercase_count > 0 and uppercase_count > 0:
                return False
        
        return True
    
    async def _get_technical_suggestions(
        self,
        doc_type: str,
        tech_analysis: Dict[str, Any]
    ) -> List[str]:
        """Get suggestions for technical documentation improvement.
        
        Args:
            doc_type: Type of documentation
            tech_analysis: Technical analysis results
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Completeness suggestions
        completeness_score = tech_analysis["completeness_score"]
        if completeness_score < 70:
            suggestions.append("Consider adding more sections like introduction, examples, and troubleshooting.")
        
        # Structure suggestions
        if tech_analysis["section_count"] < 3:
            suggestions.append("Add more sections and subheadings to improve document structure and navigation.")
        
        # Code examples suggestions
        if tech_analysis["code_block_count"] == 0 and doc_type in ["api_docs", "tutorial"]:
            suggestions.append("Add code examples to illustrate concepts and usage.")
        
        # Complexity suggestions
        complexity_score = tech_analysis["complexity_score"]
        if complexity_score > 80:
            suggestions.append("Consider breaking down complex sections into smaller, more digestible parts.")
        elif complexity_score < 30:
            suggestions.append("Add more technical depth and examples to provide comprehensive coverage.")
        
        # Documentation type specific suggestions
        if doc_type == "api_docs":
            if tech_analysis["api_endpoint_count"] == 0:
                suggestions.append("Include API endpoint documentation with request/response examples.")
            if tech_analysis["parameter_count"] == 0:
                suggestions.append("Document all parameters with types, descriptions, and examples.")
        
        elif doc_type == "tutorial":
            if tech_analysis["example_count"] < 2:
                suggestions.append("Add more practical examples and step-by-step instructions.")
        
        elif doc_type == "user_guide":
            if not tech_analysis["completeness_factors"]["has_troubleshooting"]:
                suggestions.append("Include a troubleshooting section for common issues.")
        
        # General suggestions
        suggestions.extend([
            "Consider adding a table of contents for longer documents",
            "Include links to related documentation and resources",
            "Add version information and last updated date",
            "Consider creating a quick reference or cheat sheet"
        ])
        
        return suggestions[:6]  # Limit to top 6 suggestions