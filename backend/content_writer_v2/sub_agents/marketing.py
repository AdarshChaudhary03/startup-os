"""Marketing Copy Agent

Specialized agent for generating marketing copy, ad copy, sales copy,
and promotional content with conversion optimization and persuasion techniques.
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
from ai_providers.exceptions import AIProviderError
from logging_config import log_orchestration_event

logger = logging.getLogger(__name__)


class MarketingCopyAgent(BaseContentAgent):
    """Specialized agent for marketing copy generation."""
    
    def __init__(self, config: Optional[ContentWriterV2Config] = None):
        """Initialize the Marketing Copy Agent.
        
        Args:
            config: Configuration for the agent
        """
        super().__init__(config)
        self.marketing_config = self.config.marketing
    
    async def generate_content(
        self,
        task: str,
        request_id: str,
        copy_type: str = "ad_copy",
        product_name: Optional[str] = None,
        target_audience: Optional[str] = None,
        key_benefits: Optional[List[str]] = None,
        pain_points: Optional[List[str]] = None,
        call_to_action: Optional[str] = None,
        urgency_level: Optional[str] = None,
        social_proof: Optional[List[str]] = None,
        price_point: Optional[str] = None,
        tone: Optional[ToneStyle] = None,
        brand_context: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate marketing copy content.
        
        Args:
            task: Marketing copy topic or description
            request_id: Unique request identifier
            copy_type: Type of marketing copy (ad_copy, sales_page, email, etc.)
            product_name: Name of the product/service
            target_audience: Target audience description
            key_benefits: List of key benefits to highlight
            pain_points: List of pain points to address
            call_to_action: Specific call-to-action to include
            urgency_level: Level of urgency (low, medium, high)
            social_proof: List of social proof elements
            price_point: Price information
            tone: Tone and style
            brand_context: Brand context and guidelines
            additional_instructions: Additional instructions
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with generated content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Log generation start
        log_orchestration_event(
            request_id=request_id,
            event_type="marketing_copy_generation_start",
            agent_id="marketing_copy_agent",
            message="Starting marketing copy generation",
            additional_data={
                "copy_type": copy_type,
                "product_name": product_name,
                "urgency_level": urgency_level,
                "has_benefits": bool(key_benefits),
                "has_social_proof": bool(social_proof)
            }
        )
        
        try:
            # Build marketing copy prompt
            prompt = self._build_marketing_prompt(
                task=task,
                copy_type=copy_type,
                product_name=product_name,
                target_audience=target_audience,
                key_benefits=key_benefits,
                pain_points=pain_points,
                call_to_action=call_to_action,
                urgency_level=urgency_level,
                social_proof=social_proof,
                price_point=price_point,
                tone=tone,
                brand_context=brand_context,
                additional_instructions=additional_instructions
            )
            
            # Generate marketing copy
            response = await self._generate_with_provider(
                prompt=prompt,
                request_id=request_id,
                temperature=0.8  # Higher creativity for marketing copy
            )
            
            content = response.content.strip()
            
            # Post-process marketing copy
            processed_content = await self._post_process_marketing_copy(
                content=content,
                copy_type=copy_type,
                call_to_action=call_to_action,
                urgency_level=urgency_level,
                request_id=request_id
            )
            
            # Analyze marketing copy
            copy_analysis = await self._analyze_marketing_copy(
                content=processed_content,
                copy_type=copy_type,
                key_benefits=key_benefits,
                social_proof=social_proof
            )
            
            # Build metadata
            metadata = self._extract_content_metadata(
                content=processed_content,
                copy_type=copy_type,
                product_name=product_name,
                persuasion_score=copy_analysis["persuasion_score"],
                urgency_score=copy_analysis["urgency_score"],
                benefit_count=copy_analysis["benefit_count"],
                cta_strength=copy_analysis["cta_strength"],
                tone_used=tone.value if tone else "auto"
            )
            
            result = {
                "content": processed_content,
                "metadata": metadata,
                "copy_analysis": copy_analysis,
                "variations": await self._generate_copy_variations(processed_content, copy_type, request_id),
                "suggestions": await self._get_marketing_suggestions(copy_type, copy_analysis)
            }
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="marketing_copy_generation_complete",
                agent_id="marketing_copy_agent",
                message="Marketing copy generated successfully",
                additional_data={
                    "copy_type": copy_type,
                    "content_length": len(processed_content),
                    "persuasion_score": copy_analysis["persuasion_score"],
                    "variations_count": len(result["variations"])
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="marketing_copy_generation_error",
                agent_id="marketing_copy_agent",
                message=f"Marketing copy generation failed: {str(e)}",
                additional_data={
                    "copy_type": copy_type,
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Marketing copy generation failed for request {request_id}: {e}")
            raise AIProviderError(f"Marketing copy generation failed: {str(e)}")
    
    def _build_marketing_prompt(
        self,
        task: str,
        copy_type: str,
        product_name: Optional[str],
        target_audience: Optional[str],
        key_benefits: Optional[List[str]],
        pain_points: Optional[List[str]],
        call_to_action: Optional[str],
        urgency_level: Optional[str],
        social_proof: Optional[List[str]],
        price_point: Optional[str],
        tone: Optional[ToneStyle],
        brand_context: Optional[str],
        additional_instructions: Optional[str]
    ) -> str:
        """Build a marketing copy specific prompt.
        
        Returns:
            Complete prompt string
        """
        # Copy type specific prompts
        copy_type_prompts = {
            "ad_copy": """
Create compelling advertisement copy that:
- Grabs attention with a powerful headline
- Clearly communicates the value proposition
- Addresses customer pain points directly
- Highlights key benefits and features
- Creates desire and urgency to act
- Includes a strong, clear call-to-action
- Uses persuasive language and psychology
- Optimized for conversion
""",
            "sales_page": """
Create comprehensive sales page copy that:
- Opens with an attention-grabbing headline
- Tells a compelling story or presents a problem
- Introduces the solution with clear benefits
- Addresses objections and concerns
- Includes social proof and testimonials
- Creates urgency and scarcity
- Ends with multiple strong calls-to-action
- Guides the reader through the buying journey
""",
            "email_copy": """
Create engaging email marketing copy that:
- Has a compelling subject line
- Opens with a personal, engaging hook
- Provides value before selling
- Uses conversational, friendly tone
- Includes clear call-to-action
- Optimized for email best practices
- Encourages opens, clicks, and conversions
""",
            "landing_page": """
Create high-converting landing page copy that:
- Matches the traffic source expectation
- Has a clear, benefit-focused headline
- Uses scannable formatting with bullets
- Addresses visitor objections
- Includes trust signals and social proof
- Has a prominent, action-oriented CTA
- Minimizes distractions and friction
""",
            "product_description": """
Create compelling product description copy that:
- Highlights key features and benefits
- Addresses customer needs and use cases
- Uses sensory language to help visualization
- Includes technical specifications when relevant
- Builds desire while maintaining accuracy
- Ends with a compelling reason to purchase
- Optimized for both users and search engines
"""
        }
        
        system_prompt = copy_type_prompts.get(copy_type, copy_type_prompts["ad_copy"])
        
        # Add persuasion techniques based on config
        if self.marketing_config.include_urgency:
            system_prompt += "\n- Create appropriate urgency and scarcity"
        
        if self.marketing_config.include_social_proof:
            system_prompt += "\n- Incorporate social proof elements naturally"
        
        if self.marketing_config.include_benefits:
            system_prompt += "\n- Focus on benefits over features"
        
        # Tone instructions
        tone_instructions = ""
        if tone:
            tone_map = {
                ToneStyle.PROFESSIONAL: "Maintain a professional, trustworthy tone.",
                ToneStyle.CASUAL: "Use a casual, approachable tone.",
                ToneStyle.FRIENDLY: "Be warm and friendly in your approach.",
                ToneStyle.AUTHORITATIVE: "Use an authoritative, expert tone.",
                ToneStyle.CONVERSATIONAL: "Write as if speaking directly to the customer.",
                ToneStyle.PERSUASIVE: "Use highly persuasive language and techniques.",
                ToneStyle.URGENT: "Create urgency and immediate action."
            }
            tone_instructions = tone_map.get(tone, "")
        
        # Build requirements
        requirements = []
        requirements.append(f"Topic/Product: {task}")
        requirements.append(f"Copy type: {copy_type}")
        
        if product_name:
            requirements.append(f"Product name: {product_name}")
        
        if target_audience:
            requirements.append(f"Target audience: {target_audience}")
        
        if key_benefits:
            requirements.append(f"Key benefits to highlight: {', '.join(key_benefits)}")
        
        if pain_points:
            requirements.append(f"Pain points to address: {', '.join(pain_points)}")
        
        if call_to_action:
            requirements.append(f"Call-to-action: {call_to_action}")
        
        if urgency_level:
            urgency_map = {
                "low": "Create mild urgency without being pushy",
                "medium": "Create moderate urgency with time-sensitive offers",
                "high": "Create strong urgency with limited-time offers and scarcity"
            }
            requirements.append(f"Urgency level: {urgency_map.get(urgency_level, urgency_level)}")
        
        if social_proof:
            requirements.append(f"Social proof elements to include: {', '.join(social_proof)}")
        
        if price_point:
            requirements.append(f"Price information: {price_point}")
        
        if tone_instructions:
            requirements.append(f"Tone: {tone_instructions}")
        
        if brand_context:
            requirements.append(f"Brand context: {brand_context}")
        
        if additional_instructions:
            requirements.append(f"Additional instructions: {additional_instructions}")
        
        # Combine all parts
        prompt_parts = [system_prompt]
        prompt_parts.append("\nSpecific requirements:")
        prompt_parts.extend([f"- {req}" for req in requirements])
        
        prompt_parts.append(
            "\nCreate compelling, conversion-focused copy that persuades the target audience "
            "to take action while maintaining authenticity and trust."
        )
        
        return "\n".join(prompt_parts)
    
    async def _post_process_marketing_copy(
        self,
        content: str,
        copy_type: str,
        call_to_action: Optional[str],
        urgency_level: Optional[str],
        request_id: str
    ) -> str:
        """Post-process marketing copy for optimization.
        
        Args:
            content: Generated marketing copy
            copy_type: Type of copy
            call_to_action: Specified CTA
            urgency_level: Urgency level
            request_id: Request identifier
        
        Returns:
            Post-processed copy
        """
        processed_content = content
        
        # Ensure strong CTA if not present
        if call_to_action and call_to_action.lower() not in processed_content.lower():
            processed_content += f"\n\n{call_to_action}"
        
        # Format for copy readability
        processed_content = self._format_marketing_copy(processed_content, copy_type)
        
        return processed_content.strip()
    
    def _format_marketing_copy(self, content: str, copy_type: str) -> str:
        """Format marketing copy for better readability and impact.
        
        Args:
            content: Copy content
            copy_type: Type of copy
        
        Returns:
            Formatted copy
        """
        # Add strategic formatting based on copy type
        if copy_type in ["sales_page", "landing_page"]:
            # Add more spacing for web copy
            import re
            content = re.sub(r'\n([A-Z])', r'\n\n\1', content)
        
        return content
    
    async def _analyze_marketing_copy(
        self,
        content: str,
        copy_type: str,
        key_benefits: Optional[List[str]],
        social_proof: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Analyze marketing copy for effectiveness metrics.
        
        Args:
            content: Copy content
            copy_type: Type of copy
            key_benefits: Key benefits that should be included
            social_proof: Social proof elements
        
        Returns:
            Analysis results
        """
        word_count = len(content.split())
        char_count = len(content)
        
        # Count persuasive elements
        content_lower = content.lower()
        
        # Urgency words
        urgency_words = ['now', 'today', 'limited', 'hurry', 'fast', 'quick', 'immediate', 'urgent', 'deadline']
        urgency_count = sum(1 for word in urgency_words if word in content_lower)
        urgency_score = min(100, urgency_count * 20)
        
        # Benefit words
        benefit_words = ['benefit', 'advantage', 'value', 'save', 'gain', 'improve', 'better', 'best', 'free']
        benefit_count = sum(1 for word in benefit_words if word in content_lower)
        
        # CTA strength
        cta_words = ['buy', 'order', 'get', 'start', 'join', 'subscribe', 'download', 'claim', 'try']
        cta_count = sum(1 for word in cta_words if word in content_lower)
        cta_strength = min(100, cta_count * 25)
        
        # Social proof indicators
        social_proof_words = ['testimonial', 'review', 'customer', 'client', 'trusted', 'proven', 'guarantee']
        social_proof_count = sum(1 for word in social_proof_words if word in content_lower)
        
        # Calculate overall persuasion score
        persuasion_score = (
            (urgency_score * 0.3) +
            (cta_strength * 0.4) +
            (min(100, benefit_count * 15) * 0.2) +
            (min(100, social_proof_count * 20) * 0.1)
        )
        
        # Check if key benefits are mentioned
        benefits_mentioned = 0
        if key_benefits:
            for benefit in key_benefits:
                if benefit.lower() in content_lower:
                    benefits_mentioned += 1
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "persuasion_score": round(persuasion_score, 1),
            "urgency_score": urgency_score,
            "urgency_word_count": urgency_count,
            "benefit_count": benefit_count,
            "cta_strength": cta_strength,
            "cta_word_count": cta_count,
            "social_proof_indicators": social_proof_count,
            "benefits_mentioned": benefits_mentioned,
            "benefit_coverage_percentage": round((benefits_mentioned / max(len(key_benefits), 1)) * 100, 1) if key_benefits else 0,
            "copy_type": copy_type,
            "readability_score": self._calculate_readability_score(content)
        }
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate a simple readability score.
        
        Args:
            content: Content to analyze
        
        Returns:
            Readability score
        """
        import re
        
        sentences = len(re.findall(r'[.!?]+', content))
        words = len(content.split())
        
        if sentences == 0:
            return 50.0
        
        avg_sentence_length = words / sentences
        
        # Simple readability approximation
        # Lower sentence length = higher readability
        readability = max(0, min(100, 100 - (avg_sentence_length - 15) * 2))
        
        return round(readability, 1)
    
    async def _generate_copy_variations(
        self,
        original_content: str,
        copy_type: str,
        request_id: str,
        variation_count: int = 3
    ) -> List[Dict[str, str]]:
        """Generate variations of the marketing copy for A/B testing.
        
        Args:
            original_content: Original copy content
            copy_type: Type of copy
            request_id: Request identifier
            variation_count: Number of variations to generate
        
        Returns:
            List of copy variations
        """
        variations = []
        
        variation_prompts = [
            "Create a shorter, more direct version focusing on urgency",
            "Create a longer version with more benefits and social proof",
            "Create a version with a different emotional appeal"
        ]
        
        for i, variation_prompt in enumerate(variation_prompts[:variation_count]):
            try:
                prompt = f"""
Based on this {copy_type}:

{original_content}

{variation_prompt}

Maintain the same core message but change the approach, tone, or structure.
Ensure the variation is distinct but equally compelling.
"""
                
                response = await self._generate_with_provider(
                    prompt=prompt,
                    request_id=f"{request_id}_var_{i+1}",
                    temperature=0.9,  # Higher creativity for variations
                    max_tokens=1024
                )
                
                variations.append({
                    "variation_id": f"variation_{i+1}",
                    "approach": variation_prompt,
                    "content": response.content.strip()
                })
                
            except Exception as e:
                logger.warning(f"Failed to generate variation {i+1}: {e}")
                continue
        
        return variations
    
    async def _get_marketing_suggestions(
        self,
        copy_type: str,
        copy_analysis: Dict[str, Any]
    ) -> List[str]:
        """Get suggestions for marketing copy improvement.
        
        Args:
            copy_type: Type of copy
            copy_analysis: Copy analysis results
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Persuasion score suggestions
        persuasion_score = copy_analysis["persuasion_score"]
        if persuasion_score < 50:
            suggestions.append("Consider adding more persuasive elements like urgency, benefits, and stronger CTAs.")
        
        # Urgency suggestions
        if copy_analysis["urgency_score"] < 30:
            suggestions.append("Add urgency elements like limited-time offers or scarcity to encourage immediate action.")
        
        # CTA suggestions
        if copy_analysis["cta_strength"] < 50:
            suggestions.append("Strengthen your call-to-action with more action-oriented and compelling language.")
        
        # Benefit suggestions
        if copy_analysis["benefit_count"] < 3:
            suggestions.append("Highlight more benefits to show value to your target audience.")
        
        # Social proof suggestions
        if copy_analysis["social_proof_indicators"] == 0:
            suggestions.append("Add social proof elements like testimonials, reviews, or trust indicators.")
        
        # Copy type specific suggestions
        if copy_type == "ad_copy":
            suggestions.extend([
                "Test different headlines to optimize click-through rates",
                "Consider creating multiple ad variations for A/B testing",
                "Ensure copy matches landing page message for consistency"
            ])
        elif copy_type == "sales_page":
            suggestions.extend([
                "Add more testimonials and case studies",
                "Include a money-back guarantee to reduce risk",
                "Use bullet points to highlight key benefits"
            ])
        elif copy_type == "email_copy":
            suggestions.extend([
                "Optimize subject line for higher open rates",
                "Personalize content based on subscriber data",
                "Include a clear preview text"
            ])
        
        return suggestions[:6]  # Limit to top 6 suggestions