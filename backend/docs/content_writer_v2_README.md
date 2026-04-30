# Content Writer v2 - Modular Content Generation System

A comprehensive, modular content generation system with specialized sub-agents for different content types and use cases.

## 🚀 Features

### Main Agent
- **Intelligent Task Classification**: Automatically determines the best sub-agent for any content task
- **Unified Interface**: Single entry point for all content generation needs
- **Performance Analytics**: Built-in content analysis and performance prediction
- **Caching**: Efficient sub-agent caching for improved performance

### Specialized Sub-Agents

#### 1. Social Media Agent
- **Platform-Specific**: Instagram, Twitter, LinkedIn, Facebook, TikTok, YouTube
- **Format Support**: Captions, posts, stories, reel scripts
- **Smart Hashtags**: Automatic hashtag generation with category targeting
- **Character Limits**: Platform-aware content length optimization
- **Engagement Features**: CTAs, emojis, trending elements

#### 2. Blog Agent
- **SEO Optimization**: Keyword integration, meta descriptions, structured content
- **Multiple Formats**: Blog posts, articles, long-form content
- **Content Structure**: Automatic outline generation, proper heading hierarchy
- **Readability**: Optimized for target audience and reading level

#### 3. Script Agent
- **Video Scripts**: YouTube, TikTok, Instagram Reels
- **Timing Integration**: Word-per-minute calculations, duration targeting
- **Visual Cues**: Scene descriptions, visual elements
- **Format Flexibility**: Short-form and long-form video content

#### 4. Marketing Copy Agent
- **Conversion-Focused**: Sales copy, ad copy, landing pages
- **Psychology-Driven**: Urgency, social proof, benefit highlighting
- **A/B Testing**: Multiple variations for testing
- **CTA Optimization**: Various call-to-action styles

#### 5. Technical Writing Agent
- **Documentation**: API docs, user guides, tutorials
- **Code Integration**: Code examples, technical specifications
- **Audience Targeting**: Beginner to advanced technical levels
- **Format Support**: Markdown, structured documentation

## 🏗️ Architecture

```
Content Writer v2/
├── main_agent.py          # Main orchestrator agent
├── factory.py             # Agent factory and task classification
├── config.py              # Comprehensive configuration system
├── sub_agents/            # Specialized sub-agents
│   ├── base.py           # Base agent interface
│   ├── social_media.py   # Social media content generation
│   ├── blog.py           # Blog and article generation
│   ├── script.py         # Video/audio script generation
│   ├── marketing.py      # Marketing copy generation
│   └── technical.py      # Technical documentation
├── prompts/               # Specialized prompts
│   ├── social_prompts.py # Social media prompts
│   ├── blog_prompts.py   # Blog content prompts
│   ├── script_prompts.py # Script generation prompts
│   ├── marketing_prompts.py # Marketing copy prompts
│   └── technical_prompts.py # Technical writing prompts
└── utils/                 # Utility functions
    ├── content_analyzer.py # Content analysis tools
    ├── hashtag_generator.py # Hashtag generation
    └── seo_optimizer.py   # SEO optimization tools
```

## 🚀 Quick Start

### Basic Usage

```python
from content_writer_v2 import ContentWriterMainAgent

# Initialize the main agent
agent = ContentWriterMainAgent()
await agent.initialize()

# Generate content (auto-detects appropriate sub-agent)
result = await agent.generate_content(
    task="Write an Instagram caption for a sunny day in Delhi",
    request_id="unique-request-id"
)

print(result['content'])
print(result['metadata'])
```

### Platform-Specific Social Media

```python
from content_writer_v2 import ContentAgentFactory
from content_writer_v2.config import ContentCategory, SocialPlatform

# Create social media agent
social_agent = await ContentAgentFactory.create_agent(ContentCategory.SOCIAL_MEDIA)

# Generate Instagram caption
result = await social_agent.generate_content(
    task="sunny day in Delhi",
    platform=SocialPlatform.INSTAGRAM,
    include_hashtags=True,
    include_emojis=True,
    tone="casual"
)
```

### Blog Content Generation

```python
# Create blog agent
blog_agent = await ContentAgentFactory.create_agent(ContentCategory.BLOG)

# Generate SEO-optimized blog post
result = await blog_agent.generate_content(
    task="Benefits of AI in healthcare",
    word_count=800,
    seo_keywords=["AI healthcare", "medical technology", "patient care"],
    include_outline=True
)
```

### Video Script Generation

```python
# Create script agent
script_agent = await ContentAgentFactory.create_agent(ContentCategory.SCRIPT)

# Generate reel script
result = await script_agent.generate_content(
    task="Quick morning routine tips",
    duration_seconds=30,
    script_type="reel",
    include_visual_cues=True
)
```

## ⚙️ Configuration

### Environment Variables

```bash
# AI Provider Settings
CONTENT_WRITER_PROVIDER=groq
CONTENT_WRITER_MODEL=llama-3.1-70b-versatile
CONTENT_WRITER_TEMPERATURE=0.7

# Brand Settings
BRAND_NAME="Your Brand"
BRAND_VOICE="Professional yet approachable"
TARGET_AUDIENCE="Tech-savvy millennials"

# API Keys
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

### Custom Configuration

```python
from content_writer_v2.config import ContentWriterV2Config, SocialMediaConfig

# Custom configuration
config = ContentWriterV2Config(
    brand_name="My Brand",
    brand_voice="Friendly and professional",
    social_media=SocialMediaConfig(
        include_hashtags=True,
        max_hashtags=20,
        include_emojis=True
    )
)

agent = ContentWriterMainAgent(config)
```

## 📊 Content Analysis

```python
# Analyze content performance
analysis = await agent.analyze_content_performance(
    content="Your content here",
    category=ContentCategory.SOCIAL_MEDIA,
    platform=SocialPlatform.INSTAGRAM
)

print(analysis['engagement_score'])
print(analysis['hashtag_effectiveness'])
print(analysis['readability_score'])
```

## 🔧 Extending the System

### Adding New Sub-Agents

```python
from content_writer_v2.sub_agents.base import BaseContentAgent
from content_writer_v2.config import ContentCategory

class EmailMarketingAgent(BaseContentAgent):
    async def generate_content(self, **kwargs):
        # Implementation
        pass

# Register new agent
ContentAgentFactory.register_agent(
    ContentCategory.EMAIL, 
    EmailMarketingAgent
)
```

### Custom Prompts

```python
from content_writer_v2.prompts.base import BasePromptManager

class CustomPromptManager(BasePromptManager):
    def get_custom_prompt(self, task_type: str) -> str:
        # Custom prompt logic
        pass
```

## 🧪 Testing

```python
# Test specific agent
python -m pytest tests/test_social_media_agent.py

# Test main agent
python -m pytest tests/test_main_agent.py

# Integration tests
python -m pytest tests/test_integration.py
```

## 📈 Performance Monitoring

- **Logging**: Comprehensive logging with request tracking
- **Metrics**: Content generation time, success rates, error tracking
- **Analytics**: Content performance prediction and analysis
- **Caching**: Intelligent caching for improved response times

## 🔒 Security & Privacy

- **API Key Management**: Secure environment variable handling
- **Content Validation**: Built-in content safety checks
- **Data Privacy**: No content storage, real-time generation only
- **Rate Limiting**: Built-in rate limiting for API calls

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your sub-agent or enhancement
4. Write tests
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues, feature requests, or questions:
- Create an issue in the repository
- Check the documentation
- Review existing examples

---

**Content Writer v2** - Intelligent, modular, and scalable content generation for the modern digital landscape.