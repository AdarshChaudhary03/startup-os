# API Reference Matrix for Simplified Agent Endpoints

## Overview
This document provides a comprehensive reference for the simplified agent API endpoints. These endpoints have been designed to be minimal and easy to use, requiring only essential parameters.

## Content Writer API

### Endpoint
`POST /api/simple/content_writer`

### Purpose
Generates content based on a topic and specified mode/format.

### Request Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `topic` | string | Yes | The topic to write about | "GenAI for students" |
| `mode` | string (enum) | Yes | Type of content to generate | "instagram_post" |

### Supported Modes
- `instagram_post` - Instagram post with hashtags
- `linkedin_post` - Professional LinkedIn post
- `facebook_post` - Facebook post format
- `twitter_post` - Twitter/X post (280 chars)
- `blog` - Blog article
- `article` - Long-form article
- `reel_script` - Instagram Reel script
- `youtube_script` - YouTube video script
- `email` - Email content
- `newsletter` - Newsletter content

### Example Request
```json
{
  "topic": "GenAI for students",
  "mode": "instagram_post"
}
```

### Response Format
```json
{
  "success": true,
  "content": "🚀 Discover the power of AI with GenAI for students! #AI #GenAI #Students...",
  "mode": "instagram_post",
  "topic": "GenAI for students",
  "word_count": 45,
  "hashtags": ["AI", "GenAI", "Students", "Learning"],
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### Headers
- `X-Session-ID` (optional) - Session ID for state management

---

## Social Media Publisher API

### Endpoint
`POST /api/simple/social_publisher`

### Purpose
Publishes content to specified social media platforms.

### Request Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `caption` | string | Yes | Content/caption to publish | "Check out GenAI! #AI" |
| `platform` | string (enum) | Yes | Target social media platform | "instagram" |
| `image_url` | string | No | URL of image to include | "https://example.com/image.jpg" |

### Supported Platforms
- `instagram` - Instagram posts
- `linkedin` - LinkedIn posts
- `facebook` - Facebook posts
- `twitter` - Twitter/X posts

### Example Request
```json
{
  "caption": "🚀 Discover the power of AI with GenAI for students! #AI #GenAI",
  "platform": "instagram",
  "image_url": "https://example.com/genai-image.jpg"
}
```

### Response Format
```json
{
  "success": true,
  "platform": "instagram",
  "post_id": "17841234567890",
  "post_url": "https://www.instagram.com/p/ABC123/",
  "published_at": "2024-01-20T10:35:00Z",
  "request_id": "123e4567-e89b-12d3-a456-426614174001",
  "error": null
}
```

### Headers
- `X-Session-ID` (optional) - Session ID for state management

---

## Integration Flow Example

### Step 1: Generate Content
```bash
curl -X POST http://localhost:8000/api/simple/content_writer \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: session-123" \
  -d '{
    "topic": "GenAI for students",
    "mode": "instagram_post"
  }'
```

### Step 2: Publish Content
```bash
curl -X POST http://localhost:8000/api/simple/social_publisher \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: session-123" \
  -d '{
    "caption": "[Generated content from step 1]",
    "platform": "instagram",
    "image_url": "https://example.com/image.jpg"
  }'
```

---

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid mode: unknown_mode. Supported modes are: instagram_post, linkedin_post, ..."
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "topic"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Content generation failed: [error details]"
}
```

---

## Frontend Integration Guide

### JavaScript/TypeScript Example

```javascript
// Simple API client
class SimpleAgentAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.sessionId = `session-${Date.now()}`;
  }

  async generateContent(topic, mode) {
    const response = await fetch(`${this.baseURL}/api/simple/content_writer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': this.sessionId
      },
      body: JSON.stringify({ topic, mode })
    });
    
    if (!response.ok) {
      throw new Error(`Content generation failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async publishContent(caption, platform, imageUrl = null) {
    const body = { caption, platform };
    if (imageUrl) {
      body.image_url = imageUrl;
    }

    const response = await fetch(`${this.baseURL}/api/simple/social_publisher`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': this.sessionId
      },
      body: JSON.stringify(body)
    });
    
    if (!response.ok) {
      throw new Error(`Publishing failed: ${response.statusText}`);
    }
    
    return await response.json();
  }
}

// Usage example
const api = new SimpleAgentAPI();

// Generate content
const content = await api.generateContent('GenAI for students', 'instagram_post');
console.log('Generated:', content.content);

// Publish to Instagram
const result = await api.publishContent(
  content.content,
  'instagram',
  'https://example.com/image.jpg'
);
console.log('Published:', result.post_url);
```

---

## State Management

Both endpoints support session-based state management through the `X-Session-ID` header. This allows:

1. **Content Writer** output to be automatically available to **Social Publisher**
2. Tracking of content generation and publishing workflow
3. Analytics and audit trail

### Example with State
```javascript
// The session ID links the two operations
const sessionId = 'session-123';

// Content generated with this session ID...
const content = await generateContent('AI Ethics', 'linkedin_post', sessionId);

// ...is automatically available to the publisher
const published = await publishContent(
  content.content,  // Or can use content from state
  'linkedin',
  null,
  sessionId
);
```

---

## Rate Limits and Best Practices

1. **Rate Limiting**: 
   - Content Writer: 60 requests per minute
   - Social Publisher: 30 requests per minute

2. **Best Practices**:
   - Always include session ID for workflow tracking
   - Validate content length for platform limits
   - Handle errors gracefully with retries
   - Cache generated content when possible

3. **Platform-Specific Limits**:
   - Instagram: 2,200 characters
   - Twitter: 280 characters
   - LinkedIn: 3,000 characters
   - Facebook: 63,206 characters

---

## Migration from Old API

### Old Content Writer Request
```json
{
  "task": "Write an Instagram post about GenAI for students",
  "context": {...},
  "metadata": {...}
}
```

### New Content Writer Request
```json
{
  "topic": "GenAI for students",
  "mode": "instagram_post"
}
```

### Old Social Publisher Request
```json
{
  "task": "Schedule and publish the post on Instagram",
  "context": {
    "content_writer_output": "...",
    "caption": "..."
  },
  "metadata": {...}
}
```

### New Social Publisher Request
```json
{
  "caption": "[The actual content to publish]",
  "platform": "instagram",
  "image_url": "https://example.com/image.jpg"
}
```