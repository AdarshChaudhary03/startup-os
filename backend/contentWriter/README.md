# Content Writer Agent

The Content Writer Agent is a specialized AI-powered agent that generates high-quality content using Large Language Models (LLMs) instead of dummy data. It integrates with the Groq provider to create various types of content including blog posts, articles, newsletters, and marketing copy.

## Features

### 🎯 Content Types Supported
- **Blog Posts**: Comprehensive blog content with SEO optimization
- **Articles**: Informative articles with proper structure
- **Newsletters**: Engaging newsletter content
- **Stories**: Narrative content with compelling storytelling
- **Long-form Content**: Detailed, comprehensive content pieces
- **Social Media Copy**: Platform-optimized social content
- **Marketing Copy**: Persuasive marketing materials
- **Technical Documentation**: Clear, precise technical content
- **Product Descriptions**: Compelling product copy
- **Email Sequences**: Multi-email campaign content

### 🎨 Tone of Voice Options
- Professional
- Casual
- Friendly
- Authoritative
- Conversational
- Technical
- Creative
- Persuasive
- Informative
- Engaging

### 🚀 Key Capabilities
- **LLM Integration**: Uses Groq provider with Llama models
- **Smart Task Parsing**: Automatically detects content type and tone from task descriptions
- **SEO Optimization**: Built-in SEO metadata generation
- **Content Analytics**: Word count, reading time, and quality metrics
- **Outline Generation**: Create structured content outlines
- **Content Revision**: Revise content based on feedback
- **Health Monitoring**: Provider health checks and error handling

## Architecture

```
contentWriter/
├── __init__.py                 # Package initialization
├── content_writer_config.py    # Configuration classes and enums
├── content_prompts.py          # Prompt templates and builders
├── content_writer_agent.py     # Main agent implementation
├── content_writer_service.py   # Service layer for orchestration
└── README.md                   # This documentation
```

### Components

#### ContentWriterConfig
Configuration class that defines:
- LLM provider settings (Groq, model selection, temperature)
- Content preferences (type, tone, word count)
- SEO settings (keywords, metadata)
- Quality controls (fact-checking, readability)
- Brand guidelines (voice, audience, key messages)

#### ContentPrompts
Prompt management system with:
- System prompts for different content types
- Tone-specific modifiers
- Dynamic prompt building
- SEO optimization prompts
- Content revision prompts

#### ContentWriterAgent
Core agent implementation featuring:
- LLM provider integration
- Content generation with customizable parameters
- Outline creation
- SEO optimization
- Content revision capabilities
- Analytics and health monitoring

#### ContentWriterService
Service layer that:
- Integrates with the main orchestration system
- Replaces dummy data with real LLM-generated content
- Handles task parsing and parameter extraction
- Provides fallback mechanisms

## Usage

### Basic Content Generation

```python
from contentWriter import get_content_writer_agent, ContentWriterConfig, ContentType, ToneOfVoice

# Initialize agent with custom config
config = ContentWriterConfig(
    provider="groq",
    model="llama-3.3-70b-versatile",
    default_content_type=ContentType.BLOG_POST,
    default_tone=ToneOfVoice.PROFESSIONAL,
    default_word_count=800
)

agent = await get_content_writer_agent(config)

# Generate content
content = await agent.generate_content(
    task="Write about the future of AI in startups",
    request_id="req_123",
    content_type=ContentType.BLOG_POST,
    tone=ToneOfVoice.ENGAGING,
    word_count=600,
    target_audience="startup founders",
    seo_keywords=["AI startups", "artificial intelligence", "startup technology"]
)
```

### Service Integration

```python
from contentWriter.content_writer_service import get_content_writer_service

# Get service instance
service = await get_content_writer_service()

# Execute content task (automatically parses parameters)
content = await service.execute_content_task(
    task="Create a professional blog post about AI startup trends",
    request_id="req_456"
)
```

### Orchestration Integration

The Content Writer Agent is automatically integrated into the main orchestration system. When a task is routed to the `content_writer` agent, it will:

1. Parse the task to extract content parameters
2. Generate real content using the Groq LLM provider
3. Return high-quality, contextual content instead of dummy data
4. Fall back to dummy data if LLM generation fails

## Configuration

### Environment Variables

Ensure the following environment variables are set:

```bash
# AI Provider Configuration
AI_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Content Writer Specific (optional)
CONTENT_WRITER_MODEL=llama-3.3-70b-versatile
CONTENT_WRITER_TEMPERATURE=0.7
CONTENT_WRITER_MAX_TOKENS=2048
```

### Default Configuration

The agent uses sensible defaults:
- **Provider**: Groq
- **Model**: llama-3.3-70b-versatile
- **Temperature**: 0.7
- **Max Tokens**: 2048
- **Content Type**: Blog Post
- **Tone**: Professional
- **Word Count**: 600

## Task Parsing

The service automatically detects content parameters from task descriptions:

### Content Type Detection
- "blog", "post", "article" → Blog Post
- "newsletter", "email" → Newsletter
- "story", "narrative" → Story
- "social", "tweet" → Social Copy
- "marketing", "ad", "copy" → Marketing Copy
- "long-form", "comprehensive" → Long-form
- "technical", "documentation" → Technical Documentation
- "product", "description" → Product Description

### Tone Detection
- "professional", "formal" → Professional
- "casual", "informal" → Casual
- "friendly", "warm" → Friendly
- "authoritative", "expert" → Authoritative
- "conversational", "chat" → Conversational
- "technical", "precise" → Technical
- "creative", "imaginative" → Creative
- "persuasive", "convincing" → Persuasive
- "engaging", "dynamic" → Engaging

### Word Count Extraction
The service can extract word count from patterns like:
- "Write a 500-word article"
- "Create 800 word blog post"
- "Generate 1200-word comprehensive guide"

## Error Handling

The agent includes comprehensive error handling:

1. **Provider Failures**: Falls back to dummy data if LLM provider fails
2. **Network Issues**: Retries with exponential backoff
3. **Invalid Configurations**: Uses default values for invalid settings
4. **Content Parsing Errors**: Returns fallback content with error logging
5. **Health Monitoring**: Regular health checks ensure provider availability

## Logging and Monitoring

All operations are logged with detailed information:
- Task execution start/completion
- LLM provider interactions
- Content generation metrics
- Error conditions and fallbacks
- Performance analytics

## Testing

To test the Content Writer Agent:

```bash
# Run the backend server
python run_backend.py

# Send a request to the orchestration endpoint
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a professional blog post about AI startup trends"}'
```

The response should contain real LLM-generated content instead of dummy data for content writing tasks.

## Future Enhancements

- **Multi-language Support**: Generate content in multiple languages
- **Brand Voice Training**: Fine-tune models for specific brand voices
- **Content Templates**: Pre-defined templates for common content types
- **A/B Testing**: Generate multiple variants for testing
- **Content Scheduling**: Integration with publishing platforms
- **Plagiarism Detection**: Built-in plagiarism checking
- **Fact Verification**: Automated fact-checking capabilities
- **Image Generation**: Integration with image generation models

## Dependencies

- **AI Providers**: Groq provider integration
- **Logging**: Centralized logging system
- **Configuration**: Environment-based configuration
- **Async Support**: Full async/await support for scalability

## Support

For issues or questions about the Content Writer Agent:
1. Check the logs for detailed error information
2. Verify Groq API key and provider configuration
3. Test provider health using the health check endpoint
4. Review task parsing logic for parameter extraction
