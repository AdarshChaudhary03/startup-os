"""Content Writer Agent Prompts

Pre-defined prompts and templates for different content types
to ensure consistent and high-quality content generation.
"""

from typing import Dict, Optional
from .content_writer_config import ContentType, ToneOfVoice


class ContentPrompts:
    """Collection of prompts for different content types and scenarios."""
    
    # Base system prompt for the Content Writer Agent
    SYSTEM_PROMPT = """
You are an expert Content Writer Agent specializing in creating high-quality, engaging content.

Your capabilities include:
- Writing compelling blog posts, articles, and long-form content
- Creating engaging newsletters and email sequences
- Developing marketing copy and social media content
- Adapting tone and style to match brand guidelines
- Incorporating SEO best practices naturally
- Structuring content for maximum readability and engagement

Always follow these principles:
1. Write for the target audience first, search engines second
2. Use clear, concise language that's easy to understand
3. Include compelling headlines and subheadings
4. Add value with actionable insights or useful information
5. Maintain consistency with brand voice and messaging
6. Structure content with proper flow and logical progression
7. Include relevant calls-to-action when appropriate
"""
    
    # Content type specific prompts
    CONTENT_TYPE_PROMPTS = {
        ContentType.BLOG_POST: """
Create a comprehensive blog post that:
- Has an attention-grabbing headline
- Includes an engaging introduction that hooks the reader
- Uses clear subheadings to break up content
- Provides valuable, actionable information
- Includes relevant examples or case studies
- Ends with a strong conclusion and call-to-action
- Is optimized for SEO without keyword stuffing
""",
        
        ContentType.ARTICLE: """
Write an informative article that:
- Establishes credibility and expertise on the topic
- Presents information in a logical, easy-to-follow structure
- Uses data, research, or expert quotes to support points
- Maintains objectivity while being engaging
- Includes proper citations where relevant
- Concludes with key takeaways or next steps
""",
        
        ContentType.NEWSLETTER: """
Craft an engaging newsletter that:
- Opens with a personal, conversational tone
- Highlights the most important updates or insights
- Uses scannable formatting with bullet points or short paragraphs
- Includes clear calls-to-action
- Maintains brand personality throughout
- Ends with a memorable sign-off
""",
        
        ContentType.STORY: """
Tell a compelling story that:
- Has a clear beginning, middle, and end
- Uses descriptive language to paint vivid pictures
- Includes relatable characters or situations
- Builds tension or interest throughout
- Delivers a satisfying conclusion with a clear message
- Connects emotionally with the audience
""",
        
        ContentType.LONG_FORM: """
Develop comprehensive long-form content that:
- Thoroughly explores the topic from multiple angles
- Uses a clear hierarchical structure with sections and subsections
- Includes detailed explanations and examples
- Maintains reader interest despite length
- Provides comprehensive value that justifies the word count
- Includes a table of contents or summary for easy navigation
""",
        
        ContentType.SOCIAL_COPY: """
Create engaging social media copy that:
- Captures attention immediately
- Is concise and platform-appropriate
- Includes relevant hashtags naturally
- Encourages engagement (likes, shares, comments)
- Maintains brand voice in a casual format
- Includes a clear call-to-action when needed
""",
        
        ContentType.MARKETING_COPY: """
Write persuasive marketing copy that:
- Clearly communicates the value proposition
- Addresses customer pain points directly
- Uses compelling headlines and subheadings
- Includes social proof or testimonials when relevant
- Creates urgency or desire to take action
- Ends with a strong, clear call-to-action
""",
        
        ContentType.TECHNICAL_DOCUMENTATION: """
Create clear technical documentation that:
- Uses precise, unambiguous language
- Follows a logical step-by-step structure
- Includes code examples or screenshots when helpful
- Anticipates common questions or issues
- Is organized for easy reference and searching
- Maintains accuracy while being accessible
""",
        
        ContentType.PRODUCT_DESCRIPTION: """
Write compelling product descriptions that:
- Highlight key features and benefits clearly
- Address customer needs and use cases
- Use sensory language to help customers visualize the product
- Include technical specifications when relevant
- Build desire while maintaining accuracy
- End with a compelling reason to purchase
""",
        
        ContentType.EMAIL_SEQUENCE: """
Develop an effective email sequence that:
- Maintains consistent messaging across emails
- Builds relationship and trust progressively
- Provides value in each email, not just sales pitches
- Uses personalization and segmentation appropriately
- Includes clear calls-to-action in each email
- Follows email marketing best practices
"""
    }
    
    # Tone-specific modifiers
    TONE_MODIFIERS = {
        ToneOfVoice.PROFESSIONAL: "Use a professional, authoritative tone that builds trust and credibility.",
        ToneOfVoice.CASUAL: "Write in a casual, relaxed tone that feels like a conversation with a friend.",
        ToneOfVoice.FRIENDLY: "Adopt a warm, friendly tone that makes readers feel welcome and valued.",
        ToneOfVoice.AUTHORITATIVE: "Use an authoritative, expert tone that demonstrates deep knowledge and experience.",
        ToneOfVoice.CONVERSATIONAL: "Write in a conversational style that engages readers as if speaking directly to them.",
        ToneOfVoice.TECHNICAL: "Use precise, technical language appropriate for an expert audience.",
        ToneOfVoice.CREATIVE: "Be creative and imaginative in your approach, using unique angles and creative expression.",
        ToneOfVoice.PERSUASIVE: "Use persuasive language that motivates readers to take action.",
        ToneOfVoice.INFORMATIVE: "Focus on providing clear, accurate information in an educational manner.",
        ToneOfVoice.ENGAGING: "Write in an engaging, dynamic style that captures and holds attention."
    }
    
    @classmethod
    def build_content_prompt(
        cls,
        content_type: ContentType,
        tone: ToneOfVoice,
        topic: str,
        word_count: int,
        target_audience: Optional[str] = None,
        key_points: Optional[list] = None,
        brand_voice: Optional[str] = None,
        seo_keywords: Optional[list] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Build a comprehensive prompt for content generation.
        
        Args:
            content_type: Type of content to create
            tone: Tone of voice to use
            topic: Main topic or subject
            word_count: Target word count
            target_audience: Description of target audience
            key_points: List of key points to cover
            brand_voice: Brand voice guidelines
            seo_keywords: SEO keywords to incorporate
            additional_instructions: Any additional specific instructions
        
        Returns:
            Complete prompt string for LLM
        """
        prompt_parts = [cls.SYSTEM_PROMPT]
        
        # Add content type specific instructions
        if content_type in cls.CONTENT_TYPE_PROMPTS:
            prompt_parts.append(cls.CONTENT_TYPE_PROMPTS[content_type])
        
        # Add tone modifier
        if tone in cls.TONE_MODIFIERS:
            prompt_parts.append(cls.TONE_MODIFIERS[tone])
        
        # Add specific requirements
        requirements = []
        requirements.append(f"Topic: {topic}")
        requirements.append(f"Target word count: {word_count} words")
        
        if target_audience:
            requirements.append(f"Target audience: {target_audience}")
        
        if key_points:
            requirements.append(f"Key points to cover: {', '.join(key_points)}")
        
        if brand_voice:
            requirements.append(f"Brand voice guidelines: {brand_voice}")
        
        if seo_keywords:
            requirements.append(f"SEO keywords to naturally incorporate: {', '.join(seo_keywords)}")
        
        if additional_instructions:
            requirements.append(f"Additional instructions: {additional_instructions}")
        
        # Combine all parts
        prompt_parts.append("\nSpecific requirements for this content:")
        prompt_parts.extend([f"- {req}" for req in requirements])
        
        # Add final instruction
        prompt_parts.append(
            "\nPlease create the content according to these specifications. "
            "Focus on delivering high value to the reader while meeting all requirements."
        )
        
        return "\n\n".join(prompt_parts)
    
    @classmethod
    def get_outline_prompt(cls, topic: str, content_type: ContentType) -> str:
        """Generate a prompt for creating a content outline.
        
        Args:
            topic: Main topic for the outline
            content_type: Type of content
        
        Returns:
            Prompt for outline generation
        """
        return f"""
Create a detailed outline for a {content_type.value.replace('_', ' ')} on the topic: {topic}

The outline should include:
1. A compelling headline/title
2. Main sections with descriptive headings
3. Key points to cover in each section
4. Suggested word count for each section
5. Call-to-action placement recommendations

Format the outline clearly with proper hierarchy and numbering.
"""
    
    @classmethod
    def get_seo_optimization_prompt(cls, content: str, keywords: list) -> str:
        """Generate a prompt for SEO optimization of existing content.
        
        Args:
            content: Existing content to optimize
            keywords: Target keywords
        
        Returns:
            Prompt for SEO optimization
        """
        return f"""
Optimize the following content for SEO while maintaining its quality and readability:

Target keywords: {', '.join(keywords)}

Original content:
{content}

Please:
1. Naturally incorporate the target keywords
2. Suggest an SEO-optimized title (under 60 characters)
3. Create a meta description (under 160 characters)
4. Recommend heading structure improvements
5. Suggest internal linking opportunities
6. Maintain the original tone and value

Provide the optimized content along with your SEO recommendations.
"""
    
    @classmethod
    def get_revision_prompt(cls, content: str, feedback: str) -> str:
        """Generate a prompt for content revision based on feedback.
        
        Args:
            content: Original content
            feedback: Feedback for improvement
        
        Returns:
            Prompt for content revision
        """
        return f"""
Revise the following content based on the provided feedback:

Feedback: {feedback}

Original content:
{content}

Please:
1. Address all points mentioned in the feedback
2. Maintain the overall structure and flow
3. Preserve the original tone and style
4. Ensure the revised content is cohesive
5. Highlight the changes you made

Provide the revised content along with a summary of changes made.
"""
