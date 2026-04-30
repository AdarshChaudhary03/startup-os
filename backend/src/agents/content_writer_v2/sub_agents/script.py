"""Script Content Agent

Specialized agent for generating video scripts, reel scripts, and audio content
with timing, visual cues, and platform-specific optimizations.
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


class ScriptAgent(BaseContentAgent):
    """Specialized agent for script content generation."""
    
    def __init__(self, config: Optional[ContentWriterV2Config] = None):
        """Initialize the Script Agent.
        
        Args:
            config: Configuration for the agent
        """
        super().__init__(config)
        self.script_config = self.config.script
    
    async def generate_content(
        self,
        task: str,
        request_id: str,
        script_type: str = "reel",
        duration_seconds: Optional[int] = None,
        include_visual_cues: Optional[bool] = None,
        include_timing: Optional[bool] = None,
        tone: Optional[ToneStyle] = None,
        target_audience: Optional[str] = None,
        brand_context: Optional[str] = None,
        additional_instructions: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate script content.
        
        Args:
            task: Script topic or description
            request_id: Unique request identifier
            script_type: Type of script (reel, youtube_short, etc.)
            duration_seconds: Target duration in seconds
            include_visual_cues: Whether to include visual cues
            include_timing: Whether to include timing markers
            tone: Tone and style
            target_audience: Target audience description
            brand_context: Brand context and guidelines
            additional_instructions: Additional instructions
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with generated content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Use defaults from config
        duration_seconds = duration_seconds or self.script_config.default_duration_seconds
        include_visual_cues = include_visual_cues if include_visual_cues is not None else self.script_config.include_visual_cues
        include_timing = include_timing if include_timing is not None else self.script_config.include_timing
        
        # Log generation start
        log_orchestration_event(
            request_id=request_id,
            event_type="script_generation_start",
            agent_id="script_agent",
            message="Starting script content generation",
            additional_data={
                "script_type": script_type,
                "duration_seconds": duration_seconds,
                "include_visual_cues": include_visual_cues,
                "include_timing": include_timing
            }
        )
        
        try:
            # Build script prompt
            prompt = self._build_script_prompt(
                task=task,
                script_type=script_type,
                duration_seconds=duration_seconds,
                include_visual_cues=include_visual_cues,
                include_timing=include_timing,
                tone=tone,
                target_audience=target_audience,
                brand_context=brand_context,
                additional_instructions=additional_instructions
            )
            
            # Generate script content
            response = await self._generate_with_provider(
                prompt=prompt,
                request_id=request_id,
                temperature=0.8  # Higher creativity for scripts
            )
            
            content = response.content.strip()
            
            # Post-process script
            processed_content = await self._post_process_script(
                content=content,
                script_type=script_type,
                duration_seconds=duration_seconds,
                include_timing=include_timing,
                request_id=request_id
            )
            
            # Analyze script
            script_analysis = await self._analyze_script_content(
                content=processed_content,
                target_duration=duration_seconds,
                script_type=script_type
            )
            
            # Build metadata
            metadata = self._extract_content_metadata(
                content=processed_content,
                script_type=script_type,
                target_duration_seconds=duration_seconds,
                estimated_duration_seconds=script_analysis["estimated_duration_seconds"],
                word_count=script_analysis["word_count"],
                scene_count=script_analysis["scene_count"],
                has_visual_cues=script_analysis["has_visual_cues"],
                has_timing=script_analysis["has_timing"],
                tone_used=tone.value if tone else "auto"
            )
            
            result = {
                "content": processed_content,
                "metadata": metadata,
                "script_analysis": script_analysis,
                "suggestions": await self._get_script_suggestions(script_type, script_analysis)
            }
            
            # Log successful generation
            log_orchestration_event(
                request_id=request_id,
                event_type="script_generation_complete",
                agent_id="script_agent",
                message="Script content generated successfully",
                additional_data={
                    "script_type": script_type,
                    "estimated_duration": script_analysis["estimated_duration_seconds"],
                    "target_duration": duration_seconds,
                    "scene_count": script_analysis["scene_count"]
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            log_orchestration_event(
                request_id=request_id,
                event_type="script_generation_error",
                agent_id="script_agent",
                message=f"Script content generation failed: {str(e)}",
                additional_data={
                    "script_type": script_type,
                    "error_type": type(e).__name__
                }
            )
            logger.error(f"Script content generation failed for request {request_id}: {e}")
            raise AIProviderError(f"Script content generation failed: {str(e)}")
    
    def _build_script_prompt(
        self,
        task: str,
        script_type: str,
        duration_seconds: int,
        include_visual_cues: bool,
        include_timing: bool,
        tone: Optional[ToneStyle],
        target_audience: Optional[str],
        brand_context: Optional[str],
        additional_instructions: Optional[str]
    ) -> str:
        """Build a script-specific prompt.
        
        Returns:
            Complete prompt string
        """
        # Script type specific prompts
        script_type_prompts = {
            "reel": f"""
Create an engaging Instagram Reel script for {duration_seconds} seconds that:
- Hooks viewers in the first 3 seconds
- Delivers value quickly and concisely
- Uses trending audio/music concepts
- Includes visual transitions and cuts
- Encourages engagement (likes, shares, saves)
- Follows the reel format with quick pacing
""",
            "youtube_short": f"""
Create a YouTube Shorts script for {duration_seconds} seconds that:
- Grabs attention immediately
- Delivers clear value or entertainment
- Uses YouTube-specific language and trends
- Includes engaging visuals and transitions
- Encourages subscriptions and engagement
- Optimized for vertical video format
""",
            "tiktok": f"""
Create a TikTok script for {duration_seconds} seconds that:
- Uses trending sounds and hashtags
- Follows TikTok's fast-paced style
- Includes popular TikTok formats and trends
- Encourages duets, stitches, and shares
- Uses TikTok-specific language and culture
- Optimized for the For You Page algorithm
""",
            "youtube_video": f"""
Create a YouTube video script for {duration_seconds} seconds that:
- Has a compelling introduction and hook
- Provides substantial value or entertainment
- Includes clear structure with segments
- Encourages likes, comments, and subscriptions
- Uses YouTube best practices for retention
- Includes call-to-actions throughout
""",
            "podcast": f"""
Create a podcast script segment for {duration_seconds} seconds that:
- Uses conversational, audio-friendly language
- Includes natural speech patterns and pauses
- Provides clear value through audio only
- Uses storytelling techniques
- Includes smooth transitions between topics
- Optimized for audio consumption
"""
        }
        
        system_prompt = script_type_prompts.get(script_type, script_type_prompts["reel"])
        
        # Add timing and visual cue instructions
        if include_timing:
            system_prompt += "\n- Include timing markers (e.g., [0:00-0:03]) for each segment"
        
        if include_visual_cues:
            system_prompt += "\n- Include visual cues in brackets [Visual: description]"
        
        # Tone instructions
        tone_instructions = ""
        if tone:
            tone_map = {
                ToneStyle.CASUAL: "Use a relaxed, informal speaking style.",
                ToneStyle.ENERGETIC: "Be high-energy and enthusiastic.",
                ToneStyle.PROFESSIONAL: "Maintain a professional presentation style.",
                ToneStyle.HUMOROUS: "Include appropriate humor and entertainment.",
                ToneStyle.EDUCATIONAL: "Focus on teaching and explaining clearly.",
                ToneStyle.INSPIRATIONAL: "Be motivating and uplifting.",
                ToneStyle.TRENDY: "Use current slang and trending language."
            }
            tone_instructions = tone_map.get(tone, "")
        
        # Build requirements
        requirements = []
        requirements.append(f"Topic/Content: {task}")
        requirements.append(f"Duration: {duration_seconds} seconds")
        requirements.append(f"Script type: {script_type}")
        
        if tone_instructions:
            requirements.append(f"Tone: {tone_instructions}")
        
        if target_audience:
            requirements.append(f"Target audience: {target_audience}")
        
        if brand_context:
            requirements.append(f"Brand context: {brand_context}")
        
        if additional_instructions:
            requirements.append(f"Additional instructions: {additional_instructions}")
        
        # Calculate estimated word count based on speaking rate
        words_per_minute = self.script_config.words_per_minute
        estimated_words = int((duration_seconds / 60) * words_per_minute)
        requirements.append(f"Target word count: approximately {estimated_words} words")
        
        # Combine all parts
        prompt_parts = [system_prompt]
        prompt_parts.append("\nSpecific requirements:")
        prompt_parts.extend([f"- {req}" for req in requirements])
        
        prompt_parts.append(
            "\nCreate an engaging, well-structured script that fits the time constraint "
            "and platform requirements. Focus on audience retention and engagement."
        )
        
        return "\n".join(prompt_parts)
    
    async def _post_process_script(
        self,
        content: str,
        script_type: str,
        duration_seconds: int,
        include_timing: bool,
        request_id: str
    ) -> str:
        """Post-process script content.
        
        Args:
            content: Generated script content
            script_type: Type of script
            duration_seconds: Target duration
            include_timing: Whether timing should be included
            request_id: Request identifier
        
        Returns:
            Post-processed script
        """
        processed_content = content
        
        # Add timing markers if requested and not present
        if include_timing and "[0:" not in processed_content:
            processed_content = await self._add_timing_markers(
                content=processed_content,
                duration_seconds=duration_seconds,
                request_id=request_id
            )
        
        # Format for script readability
        processed_content = self._format_script_structure(processed_content)
        
        return processed_content.strip()
    
    async def _add_timing_markers(
        self,
        content: str,
        duration_seconds: int,
        request_id: str
    ) -> str:
        """Add timing markers to script content.
        
        Args:
            content: Script content
            duration_seconds: Total duration
            request_id: Request identifier
        
        Returns:
            Script with timing markers
        """
        # Simple implementation - divide content into equal time segments
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return content
        
        # Calculate time per segment
        time_per_segment = duration_seconds / len(lines)
        
        timed_lines = []
        current_time = 0
        
        for line in lines:
            start_time = int(current_time)
            end_time = min(int(current_time + time_per_segment), duration_seconds)
            
            # Format time as [MM:SS-MM:SS]
            start_min, start_sec = divmod(start_time, 60)
            end_min, end_sec = divmod(end_time, 60)
            
            time_marker = f"[{start_min}:{start_sec:02d}-{end_min}:{end_sec:02d}]"
            timed_lines.append(f"{time_marker} {line}")
            
            current_time += time_per_segment
        
        return "\n".join(timed_lines)
    
    def _format_script_structure(self, content: str) -> str:
        """Format script for better readability.
        
        Args:
            content: Script content
        
        Returns:
            Formatted script
        """
        # Add proper spacing around visual cues and timing markers
        import re
        
        # Add spacing around timing markers
        content = re.sub(r'(\[\d+:\d+-\d+:\d+\])', r'\n\1', content)
        
        # Add spacing around visual cues
        content = re.sub(r'(\[Visual: [^\]]+\])', r'\n\1\n', content)
        
        # Clean up excessive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    async def _analyze_script_content(
        self,
        content: str,
        target_duration: int,
        script_type: str
    ) -> Dict[str, Any]:
        """Analyze script content for metrics.
        
        Args:
            content: Script content
            target_duration: Target duration in seconds
            script_type: Type of script
        
        Returns:
            Analysis results
        """
        word_count = len(content.split())
        char_count = len(content)
        
        # Estimate duration based on word count and speaking rate
        words_per_minute = self.script_config.words_per_minute
        estimated_duration_seconds = (word_count / words_per_minute) * 60
        
        # Count scenes/segments (lines that aren't timing markers or visual cues)
        import re
        lines = content.split('\n')
        scene_count = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith('[') and not line.endswith(']'):
                scene_count += 1
        
        # Check for timing markers and visual cues
        has_timing = bool(re.search(r'\[\d+:\d+-\d+:\d+\]', content))
        has_visual_cues = bool(re.search(r'\[Visual:', content))
        
        # Calculate duration accuracy
        duration_difference = estimated_duration_seconds - target_duration
        duration_accuracy = max(0, 100 - abs(duration_difference) / target_duration * 100)
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "estimated_duration_seconds": round(estimated_duration_seconds, 1),
            "target_duration_seconds": target_duration,
            "duration_difference_seconds": round(duration_difference, 1),
            "duration_accuracy_percentage": round(duration_accuracy, 1),
            "scene_count": scene_count,
            "has_timing": has_timing,
            "has_visual_cues": has_visual_cues,
            "script_type": script_type,
            "words_per_minute_actual": round(word_count / (estimated_duration_seconds / 60), 1) if estimated_duration_seconds > 0 else 0
        }
    
    async def _get_script_suggestions(
        self,
        script_type: str,
        script_analysis: Dict[str, Any]
    ) -> List[str]:
        """Get suggestions for script improvement.
        
        Args:
            script_type: Type of script
            script_analysis: Script analysis results
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Duration suggestions
        duration_diff = script_analysis["duration_difference_seconds"]
        if duration_diff > 10:
            suggestions.append(f"Script is {duration_diff:.1f} seconds too long. Consider condensing content.")
        elif duration_diff < -10:
            suggestions.append(f"Script is {abs(duration_diff):.1f} seconds too short. Consider adding more content.")
        
        # Scene count suggestions
        scene_count = script_analysis["scene_count"]
        if script_type in ["reel", "youtube_short", "tiktok"] and scene_count < 3:
            suggestions.append("Consider adding more scenes/cuts to maintain engagement for short-form content.")
        
        # Visual cues suggestions
        if not script_analysis["has_visual_cues"] and script_type != "podcast":
            suggestions.append("Add visual cues to help with video production and engagement.")
        
        # Timing suggestions
        if not script_analysis["has_timing"]:
            suggestions.append("Add timing markers to help with pacing during production.")
        
        # Script type specific suggestions
        if script_type == "reel":
            suggestions.extend([
                "Ensure the first 3 seconds grab attention immediately",
                "Consider trending audio or music integration",
                "Add hooks that encourage saves and shares"
            ])
        elif script_type == "youtube_short":
            suggestions.extend([
                "Include a strong call-to-action for subscriptions",
                "Consider creating a series for better discoverability",
                "Optimize for vertical video format"
            ])
        elif script_type == "tiktok":
            suggestions.extend([
                "Research current TikTok trends and sounds",
                "Consider duet or stitch opportunities",
                "Use trending hashtags in the final post"
            ])
        
        return suggestions[:5]  # Limit to top 5 suggestions