# Social Media Publisher Agent v1.0

A comprehensive social media publishing system with specialized sub-agents for different platforms.

## Overview

The Social Media Publisher Agent is designed to handle content publishing, scheduling, and distribution across multiple social media platforms. It follows a modular architecture with specialized sub-agents for each platform.

## Architecture

```
social_media_publisher/
├── main_agent.py          # Main orchestrator agent
├── factory.py             # Sub-agent factory
├── config.py              # Configuration and enums
├── sub_agents/            # Platform-specific agents
│   ├── base.py           # Abstract base class
│   ├── instagram.py      # Instagram publishing agent
│   ├── linkedin.py       # LinkedIn publishing agent
│   └── facebook.py       # Facebook publishing agent
└── README.md             # This file
```

## Features

### Main Agent

- **Platform Detection**: Automatically detects target platform from task
- **Content Optimization**: Optimizes content for each platform's requirements
- **Scheduling**: Handles post scheduling and timing optimization
- **Multi-platform Publishing**: Can publish to multiple platforms simultaneously
- **Analytics Integration**: Tracks publishing metrics and performance

### Sub-Agents

#### Instagram Agent

- **Post Types**: Feed posts, Stories, Reels
- **Hashtag Optimization**: Automatic hashtag suggestions and optimization
- **Image Processing**: Image sizing and format optimization
- **Story Features**: Polls, questions, stickers integration
- **Reel Optimization**: Video format and timing optimization

#### LinkedIn Agent

- **Post Types**: Text posts, Article publishing, Company updates
- **Professional Tone**: Business-appropriate content optimization
- **Engagement Features**: Poll creation, document sharing
- **Network Targeting**: Professional audience optimization
- **Article Publishing**: Long-form content publishing

#### Facebook Agent

- **Post Types**: Text posts, Image posts, Video posts, Events
- **Audience Targeting**: Demographic and interest-based targeting
- **Page Management**: Business page posting and management
- **Event Creation**: Event posting and promotion
- **Community Features**: Group posting and community management

## Configuration

### Environment Variables

```bash
# Social Media API Keys
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
LINKEDIN_ACCESS_TOKEN=your_linkedin_token
FACEBOOK_ACCESS_TOKEN=your_facebook_token

# Publishing Settings
SOCIAL_MEDIA_DEFAULT_PLATFORM=instagram
SOCIAL_MEDIA_AUTO_SCHEDULE=true
SOCIAL_MEDIA_OPTIMAL_TIMING=true

# Content Settings
SOCIAL_MEDIA_MAX_HASHTAGS=30
SOCIAL_MEDIA_AUTO_HASHTAGS=true
SOCIAL_MEDIA_CONTENT_MODERATION=true
```

### Platform-Specific Settings

#### Instagram

- **Character Limit**: 2,200 characters
- **Hashtag Limit**: 30 hashtags
- **Image Requirements**: 1080x1080 (square), 1080x1350 (portrait)
- **Video Requirements**: MP4, max 60 seconds for Reels

#### LinkedIn

- **Character Limit**: 3,000 characters
- **Article Length**: Up to 125,000 characters
- **Image Requirements**: 1200x627 (landscape)
- **Professional Tone**: Required

#### Facebook

- **Character Limit**: 63,206 characters
- **Image Requirements**: 1200x630 (landscape)
- **Video Requirements**: MP4, MOV, AVI
- **Event Features**: Date, time, location

## Usage Examples

### Basic Publishing

```python
from social_media_publisher import SocialMediaPublisherMainAgent

# Initialize agent
agent = SocialMediaPublisherMainAgent()
await agent.initialize()

# Publish to Instagram
result = await agent.publish_content(
    content="Check out our new product launch! 🚀",
    platform=SocialPlatform.INSTAGRAM,
    post_type=PostType.TEXT_POST,
    request_id="req_123"
)
```

### Multi-platform Publishing

```python
# Publish to multiple platforms
result = await agent.publish_content(
    content="Excited to announce our Series A funding!",
    platforms=[SocialPlatform.LINKEDIN, SocialPlatform.FACEBOOK],
    post_type=PostType.TEXT_POST,
    request_id="req_124"
)
```

### Scheduled Publishing

```python
from datetime import datetime, timedelta

# Schedule post for later
result = await agent.schedule_content(
    content="Don't miss our webinar tomorrow!",
    platform=SocialPlatform.LINKEDIN,
    schedule_time=datetime.now() + timedelta(hours=24),
    request_id="req_125"
)
```

## Task Classification

The agent automatically classifies tasks based on keywords:

- **Instagram**: "instagram", "insta", "ig", "story", "reel", "hashtag"
- **LinkedIn**: "linkedin", "professional", "business", "article", "network"
- **Facebook**: "facebook", "fb", "event", "community", "page"
- **General**: "post", "publish", "schedule", "social media"

## Error Handling

The agent includes comprehensive error handling for:

- **API Rate Limits**: Automatic retry with exponential backoff
- **Content Violations**: Content moderation and compliance checking
- **Platform Outages**: Fallback mechanisms and error reporting
- **Authentication Issues**: Token refresh and re-authentication

## Monitoring and Analytics

- **Publishing Metrics**: Success rates, engagement tracking
- **Performance Analytics**: Reach, impressions, clicks
- **Error Monitoring**: Failed posts, API errors, rate limits
- **Scheduling Analytics**: Optimal posting times, audience insights

## Integration with Content Writer

The Social Media Publisher Agent is designed to work seamlessly with the Content Writer v2:

1. **Content Creation**: Content Writer creates platform-optimized content
2. **Content Publishing**: Social Media Publisher handles distribution
3. **Workflow Integration**: Automatic handoff between agents
4. **Content Optimization**: Platform-specific formatting and optimization

## Testing

Run the test suite:

```bash
python test_social_media_publisher.py
```

## Future Enhancements

- **Twitter/X Integration**: Add Twitter publishing capabilities
- **TikTok Support**: Video content publishing to TikTok
- **Advanced Analytics**: Detailed performance metrics and insights
- **A/B Testing**: Content variation testing and optimization
- **Automated Responses**: Auto-reply to comments and messages
- **Content Calendar**: Visual content planning and scheduling
- **Influencer Collaboration**: Partnership and collaboration features
