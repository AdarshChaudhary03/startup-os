"""Blog Content Agent

Specialized agent for generating blog posts, articles, and long-form content
with SEO optimization, structured formatting, and comprehensive coverage.
"""

import re
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


class BlogAgent(BaseContentAgent):
    """Specialized agent for blog and article content generation."""
    
    def __init__(self, config: Optional[ContentWriterV2Config] = None):
        """Initialize the Blog Agent.
        
        Args:
            config: Configuration for the agent
        """
        super().__init__(config)
        self.blog_config = self.config.blog
    
    async def generate_content(
        self,
        task: str,
        request_id: str,
        content_format: Optional[ContentFormat] = None,
        tone: Optional[ToneStyle] = None,
        word_count: Optional[int] = None,
        seo_keywords: Optional[List[str]] = None,
        target_audience: Optional[str] = None,
        brand_context: Optional[str] = None,
        include_outline: Optional[bool] = None,
        include_seo_optimization: Optional[bool] = None,
        include_meta_description: Optional[bool] = None,
        content_structure: Optional[List[str]] = None,
        additional_instructions: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate blog content.
        
        Args:
            task: Blog topic or description
            request_id: Unique request identifier
            content_format: Specific content format
            tone: Tone and style
            word_count: Target word count
            seo_keywords: SEO keywords to include
            target_audience: Target audience description
            brand_context: Brand context and guidelines
            include_outline: Whether to include an outline
            include_seo_optimization: Whether to include SEO optimization
            include_meta_description: Whether to include meta description
            content_structure: Custom content structure
            additional_instructions: Additional instructions
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with generated content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Use defaults from config
        word_count = word_count or self.blog_config.default_word_count
        include_outline = include_outline if include_outline is not None else self.blog_config.include_outline
        include_seo_optimization = include_seo_optimization if include_seo_optimization is not None else self.blog_config.include_seo_optimization
        include_meta_description = include_meta_description if include_meta_description is not None else self.blog_config.include_meta_description
        content_structure = content_structure or self.blog_config.default_structure
        
        # Log generation start
        log_orchestration_event(
            request_id=request_id,
            event_type="blog_generation_start",
            agent_id="blog_agent",
            message="Starting blog content generation",
            additional_data={
                "word_count_target": word_count,
                "include_seo": include_seo_optimization,
                "include_outline": include_outline,
                "seo_keywords_count": len(seo_keywords) if seo_keywords else 0
            }
        )
        
        try:
            # Generate outline first if requested
            outline = None
            if include_outline:
                outline = await self._generate_outline(
                    task=task,
                    word_count=word_count,
                    structure=content_structure,
                    seo_keywords=seo_keywords,
                    request_id=request_id
                )
            
            # Build blog content prompt
            prompt = self._build_blog_prompt(
                task=task,
                content_format=content_format,
                tone=tone,
                word_count=word_count,
                seo_keywords=seo_keywords,
                target_audience=target_audience,
                brand_context=brand_context,
                content_structure=content_structure,
                outline=outline,
                additional_instructions=additional_instructions
            )
            
            # Generate main content
            response = await self._generate_with_provider(
                prompt=prompt,
                request_id=request_id,
                temperature=0.7,  # Balanced creativity for blog content
                max_tokens=min(4000, word_count * 2)  # Estimate tokens needed
            )
            
            content = response.content.strip()
            
            # Post-process content
            processed_content = await self._post_process_blog_content(
                content=content,
                seo_keywords=seo_keywords,
                include_seo_optimization=include_seo_optimization,
                request_id=request_id
            )
            
            # Generate SEO metadata if requested
            seo_metadata = None
            if include_seo_optimization or include_meta_description:
                seo_metadata = await self._generate_seo_metadata(
                    content=processed_content,
                    keywords=seo_keywords,
                    request_id=request_id
                )
            
            # Analyze content structure and quality
            content_analysis = await self._analyze_blog_content(
                content=processed_content,
                target_word_count=word_count,
                seo_keywords=seo_keywords
            )
            
            # Build metadata
            metadata = self._extract_content_metadata(
                content=processed_content,
                content_format=content_format.value if content_format else "blog_post",
                target_word_count=word_count,
                actual_word_count=content_analysis["word_count"],
                seo_keywords_used=content_analysis["seo_keywords_found"],
                readability_score=content_analysis["readability_score"],
                structure_score=content_analysis["structure_score"],
                tone_used=tone.value if tone else "auto"
            )
            
            result = {
                "content": processed_content,
                "outline": outline,
                "seo_metadata": seo_metadata,
                "metadata": metadata,
                "content_analysis": content_analysis,
                "suggestions": await self._get_blog_suggestions(task, content_analysis)
            }
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="blog_generation_complete",
                agent_id="blog_agent",
                message="Blog content generated successfully",
                additional_data={
                    "actual_word_count": content_analysis["word_count"],
                    "target_word_count": word_count,
                    "seo_optimized": include_seo_optimization,
                    "readability_score": content_analysis["readability_score"]
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="blog_generation_error",
                agent_id="blog_agent",
                message=f"Blog content generation failed: {str(e)}",
                additional_data={
                    "error_type": type(e).__name__,
                    "target_word_count": word_count
                }
            )
            logger.error(f"Blog content generation failed for request {request_id}: {e}")
            raise AIProviderError(f"Blog content generation failed: {str(e)}")
    
    async def _generate_outline(
        self,
        task: str,
        word_count: int,
        structure: List[str],
        seo_keywords: Optional[List[str]],
        request_id: str
    ) -> str:
        """Generate a blog outline.
        
        Args:
            task: Blog topic
            word_count: Target word count
            structure: Content structure
            seo_keywords: SEO keywords
            request_id: Request identifier
        
        Returns:
            Generated outline
        """
        outline_prompt = f"""
Create a detailed blog outline for the topic: {task}

Target word count: {word_count} words
Content structure: {', '.join(structure)}
{f"SEO keywords to incorporate: {', '.join(seo_keywords)}" if seo_keywords else ""}

The outline should include:
1. Compelling headline (H1)
2. Introduction hook and preview
3. Main sections with H2 headings
4. Subsections with H3 headings where appropriate
5. Key points to cover in each section
6. Conclusion and call-to-action
7. Estimated word count for each section

Format the outline clearly with proper hierarchy and numbering.
"""
        
        response = await self._generate_with_provider(
            prompt=outline_prompt,
            request_id=f"{request_id}_outline",
            temperature=0.6,
            max_tokens=1024
        )
        
        return response.content.strip()
    
    def _build_blog_prompt(
        self,
        task: str,
        content_format: Optional[ContentFormat] = None,
        tone: Optional[ToneStyle] = None,
        word_count: int = 800,
        seo_keywords: Optional[List[str]] = None,
        target_audience: Optional[str] = None,
        brand_context: Optional[str] = None,
        content_structure: Optional[List[str]] = None,
        outline: Optional[str] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Build a comprehensive prompt for blog content generation.
        
        Args:
            task: Blog topic
            content_format: Content format
            tone: Tone and style
            word_count: Target word count
            seo_keywords: SEO keywords
            target_audience: Target audience
            brand_context: Brand context
            content_structure: Content structure
            outline: Pre-generated outline
            additional_instructions: Additional instructions
        
        Returns:
            Complete prompt string
        """
        system_prompt = f"""
You are an expert blog writer and content strategist specializing in creating high-quality, engaging blog posts.

Create blog content that:
- Provides genuine value and actionable insights
- Uses clear, engaging writing that keeps readers interested
- Follows proper blog structure with compelling headlines
- Incorporates SEO best practices naturally
- Maintains consistent tone and voice throughout
- Uses subheadings, bullet points, and formatting for readability
- Includes relevant examples, data, or case studies
- Ends with a strong conclusion and clear call-to-action
- Stays close to the target word count of {word_count} words
"""
        
        # Content format specific instructions
        format_instructions = ""
        if content_format:
            format_map = {
                ContentFormat.BLOG_POST: "Create a comprehensive blog post with introduction, body, and conclusion.",
                ContentFormat.ARTICLE: "Write an informative article with authoritative tone and proper citations.",
            }
            format_instructions = format_map.get(content_format, "")
        
        # Tone instructions
        tone_instructions = ""
        if tone:
            tone_map = {
                ToneStyle.PROFESSIONAL: "Maintain a professional, authoritative tone throughout.",
                ToneStyle.CASUAL: "Use a conversational, approachable tone.",
                ToneStyle.FRIENDLY: "Be warm and welcoming in your writing style.",
                ToneStyle.EDUCATIONAL: "Focus on teaching and explaining concepts clearly.",
                ToneStyle.AUTHORITATIVE: "Demonstrate expertise and credibility.",
                ToneStyle.CONVERSATIONAL: "Write as if speaking directly to the reader."
            }
            tone_instructions = tone_map.get(tone, "")
        
        # Build requirements
        requirements = []
        requirements.append(f"Topic: {task}")
        requirements.append(f"Target word count: {word_count} words")
        
        if format_instructions:
            requirements.append(f"Format: {format_instructions}")
        
        if tone_instructions:
            requirements.append(f"Tone: {tone_instructions}")
        
        if seo_keywords:
            requirements.append(f"SEO keywords to naturally incorporate: {', '.join(seo_keywords)}")
            requirements.append(f"Target keyword density: {self.blog_config.seo_keyword_density}%")
        
        if target_audience:
            requirements.append(f"Target audience: {target_audience}")
        
        if brand_context:
            requirements.append(f"Brand context: {brand_context}")
        
        if content_structure:
            requirements.append(f"Content structure: {', '.join(content_structure)}")
        
        if outline:
            requirements.append(f"Follow this outline:\n{outline}")
        
        if additional_instructions:
            requirements.append(f"Additional instructions: {additional_instructions}")
        
        # Combine all parts
        prompt_parts = [system_prompt]
        prompt_parts.append("\nSpecific requirements:")
        prompt_parts.extend([f"- {req}" for req in requirements])
        
        prompt_parts.append(
            "\nWrite comprehensive, valuable blog content that meets all requirements. "
            "Focus on providing genuine value to readers while optimizing for search engines naturally."
        )
        
        return "\n".join(prompt_parts)
    
    async def _post_process_blog_content(
        self,
        content: str,
        seo_keywords: Optional[List[str]],
        include_seo_optimization: bool,
        request_id: str
    ) -> str:
        """Post-process blog content for optimization.
        
        Args:
            content: Generated content
            seo_keywords: SEO keywords
            include_seo_optimization: Whether to optimize for SEO
            request_id: Request identifier
        
        Returns:
            Post-processed content
        """
        processed_content = content
        
        # Ensure proper heading structure
        processed_content = self._fix_heading_structure(processed_content)
        
        # Add proper paragraph breaks
        processed_content = self._improve_readability(processed_content)
        
        # SEO optimization if requested
        if include_seo_optimization and seo_keywords:
            processed_content = await self._optimize_for_seo(
                content=processed_content,
                keywords=seo_keywords,
                request_id=request_id
            )
        
        return processed_content.strip()
    
    def _fix_heading_structure(self, content: str) -> str:
        """Fix heading structure for better SEO and readability.
        
        Args:
            content: Content to fix
        
        Returns:
            Content with fixed headings
        """
        # Ensure H1 is used only once (for title)
        # Convert multiple H1s to H2s
        lines = content.split('\n')
        h1_count = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('# '):
                h1_count += 1
                if h1_count > 1:
                    lines[i] = line.replace('# ', '## ', 1)
        
        return '\n'.join(lines)
    
    def _improve_readability(self, content: str) -> str:
        """Improve content readability with proper formatting.
        
        Args:
            content: Content to improve
        
        Returns:
            Improved content
        """
        # Add proper spacing around headings
        content = re.sub(r'(\n)(#{1,6} .+)(\n)', r'\1\n\2\n\n', content)
        
        # Ensure paragraphs are properly separated
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    async def _optimize_for_seo(
        self,
        content: str,
        keywords: List[str],
        request_id: str
    ) -> str:
        """Optimize content for SEO.
        
        Args:
            content: Content to optimize
            keywords: SEO keywords
            request_id: Request identifier
        
        Returns:
            SEO-optimized content
        """
        # This is a simplified SEO optimization
        # In a real implementation, you might use more sophisticated techniques
        
        optimized_content = content
        
        # Ensure primary keyword appears in the first paragraph
        if keywords:
            primary_keyword = keywords[0]
            paragraphs = optimized_content.split('\n\n')
            
            if len(paragraphs) > 1 and primary_keyword.lower() not in paragraphs[1].lower():
                # Try to naturally incorporate the keyword
                first_para = paragraphs[1]
                if not first_para.strip().startswith('#'):  # Not a heading
                    # Simple keyword insertion (could be improved)
                    optimized_content = optimized_content.replace(
                        first_para,
                        f"{first_para} This guide covers everything about {primary_keyword}.",
                        1
                    )
        
        return optimized_content
    
    async def _generate_seo_metadata(
        self,
        content: str,
        keywords: Optional[List[str]],
        request_id: str
    ) -> Dict[str, str]:
        """Generate SEO metadata for the blog post.
        
        Args:
            content: Blog content
            keywords: SEO keywords
            request_id: Request identifier
        
        Returns:
            SEO metadata dictionary
        """
        # Extract title from content
        lines = content.split('\n')
        title = "Blog Post"
        for line in lines:
            if line.strip().startswith('# '):
                title = line.replace('# ', '').strip()
                break
        
        # Generate meta description
        seo_prompt = f"""
Based on this blog content, create SEO metadata:

Title: {title}
Content preview: {content[:500]}...
{f"Target keywords: {', '.join(keywords)}" if keywords else ""}

Generate:
1. SEO-optimized title (under 60 characters)
2. Meta description (under 160 characters)
3. Focus keyword
4. Suggested slug (URL-friendly)

Format as JSON with keys: seo_title, meta_description, focus_keyword, slug
"""
        
        try:
            response = await self._generate_with_provider(
                prompt=seo_prompt,
                request_id=f"{request_id}_seo",
                temperature=0.3,
                max_tokens=512
            )
            
            import json
            seo_data = json.loads(response.content)
            return seo_data
            
        except Exception as e:
            logger.warning(f"Failed to generate SEO metadata: {e}")
            # Fallback metadata
            return {
                "seo_title": title[:60],
                "meta_description": content[:160].replace('\n', ' ').strip(),
                "focus_keyword": keywords[0] if keywords else "blog",
                "slug": re.sub(r'[^a-zA-Z0-9\s]', '', title.lower()).replace(' ', '-')
            }
    
    async def _analyze_blog_content(
        self,
        content: str,
        target_word_count: int,
        seo_keywords: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Analyze blog content for quality metrics.
        
        Args:
            content: Content to analyze
            target_word_count: Target word count
            seo_keywords: SEO keywords
        
        Returns:
            Analysis results
        """
        word_count = len(content.split())
        char_count = len(content)
        
        # Count headings
        h1_count = len(re.findall(r'^# .+', content, re.MULTILINE))
        h2_count = len(re.findall(r'^## .+', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### .+', content, re.MULTILINE))
        
        # SEO keyword analysis
        seo_keywords_found = []
        if seo_keywords:
            content_lower = content.lower()
            for keyword in seo_keywords:
                if keyword.lower() in content_lower:
                    seo_keywords_found.append(keyword)
        
        # Simple readability score (Flesch Reading Ease approximation)
        sentences = len(re.findall(r'[.!?]+', content))
        avg_sentence_length = word_count / max(sentences, 1)
        readability_score = max(0, min(100, 206.835 - (1.015 * avg_sentence_length)))
        
        # Structure score
        structure_score = 0
        if h1_count == 1:  # Good: exactly one H1
            structure_score += 25
        if h2_count >= 2:  # Good: multiple sections
            structure_score += 25
        if word_count >= target_word_count * 0.8:  # Close to target length
            structure_score += 25
        if len(seo_keywords_found) > 0:  # SEO keywords present
            structure_score += 25
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "target_word_count": target_word_count,
            "word_count_difference": word_count - target_word_count,
            "word_count_percentage": round((word_count / target_word_count) * 100, 1),
            "heading_counts": {
                "h1": h1_count,
                "h2": h2_count,
                "h3": h3_count,
                "total": h1_count + h2_count + h3_count
            },
            "seo_keywords_found": seo_keywords_found,
            "seo_keyword_coverage": len(seo_keywords_found) / max(len(seo_keywords), 1) if seo_keywords else 0,
            "readability_score": round(readability_score, 1),
            "structure_score": structure_score,
            "estimated_reading_time_minutes": max(1, round(word_count / 200)),
            "sentences_count": sentences,
            "avg_sentence_length": round(avg_sentence_length, 1)
        }
    
    async def _get_blog_suggestions(
        self,
        task: str,
        content_analysis: Dict[str, Any]
    ) -> List[str]:
        """Get suggestions for blog improvement.
        
        Args:
            task: Original task
            content_analysis: Content analysis results
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Word count suggestions
        word_diff = content_analysis["word_count_difference"]
        if word_diff < -100:
            suggestions.append(f"Consider adding more content. Current post is {abs(word_diff)} words below target.")
        elif word_diff > 200:
            suggestions.append(f"Consider condensing content. Current post is {word_diff} words above target.")
        
        # Structure suggestions
        if content_analysis["heading_counts"]["h2"] < 2:
            suggestions.append("Add more H2 headings to improve content structure and readability.")
        
        if content_analysis["heading_counts"]["h1"] != 1:
            suggestions.append("Ensure exactly one H1 heading for optimal SEO.")
        
        # SEO suggestions
        if content_analysis["seo_keyword_coverage"] < 0.5:
            suggestions.append("Consider incorporating more of the target SEO keywords naturally.")
        
        # Readability suggestions
        if content_analysis["readability_score"] < 50:
            suggestions.append("Consider shortening sentences to improve readability.")
        elif content_analysis["readability_score"] > 90:
            suggestions.append("Content might be too simple. Consider adding more sophisticated language.")
        
        # General suggestions
        suggestions.extend([
            f"Consider creating related content about {task} for a content series",
            "Add internal links to other relevant blog posts",
            "Include relevant images or infographics to enhance engagement",
            "Consider updating this content regularly to maintain SEO rankings"
        ])
        
        return suggestions[:5]  # Limit to top 5 suggestions