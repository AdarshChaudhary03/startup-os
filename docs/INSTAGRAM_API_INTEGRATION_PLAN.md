# Instagram API Integration Plan

## Current Issue Analysis

The Social Media Publisher Agent is currently using simulation for Instagram posting instead of actual Instagram API integration. The logs show:

```
2026-04-29 14:19:59,290 - social_media_publisher.sub_agents.instagram - INFO - Successfully published to Instagram: ig_f7e2cd137ef4 - its not been actually posted on instagram, need to remove simulation and use actual endpoints to post it to instagram.
```

## Instagram API Options

### 1. Instagram Basic Display API
- **Purpose**: Read-only access to user media
- **Limitations**: Cannot create posts, only read existing content
- **Not suitable for publishing**

### 2. Instagram Graph API
- **Purpose**: Full publishing capabilities for Instagram Business accounts
- **Requirements**: 
  - Facebook App with Instagram Graph API permissions
  - Instagram Business Account
  - Facebook Page connected to Instagram account
  - Valid access tokens

### 3. Third-Party Services
- **Buffer API**: Comprehensive social media scheduling
- **Hootsuite API**: Enterprise social media management
- **Later API**: Visual content scheduling
- **Creator Studio API**: Facebook's native scheduling tool

## Recommended Implementation: Instagram Graph API

### Required Setup

1. **Facebook App Configuration**
   - Create Facebook App at developers.facebook.com
   - Add Instagram Graph API product
   - Configure permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`

2. **Instagram Business Account**
   - Convert personal Instagram to Business account
   - Connect to Facebook Page
   - Verify business information

3. **Authentication Flow**
   - Implement OAuth 2.0 flow
   - Exchange authorization code for access token
   - Store and refresh tokens securely

### API Endpoints for Publishing

1. **Create Media Container**
   ```
   POST /{ig-user-id}/media
   ```

2. **Publish Media Container**
   ```
   POST /{ig-user-id}/media_publish
   ```

3. **Upload Media (for images/videos)**
   ```
   POST /{ig-user-id}/media
   ```

### Implementation Steps

1. **Update Configuration**
   - Add Instagram Graph API credentials
   - Configure webhook endpoints
   - Set up token refresh mechanism

2. **Implement Authentication**
   - OAuth 2.0 flow for initial authorization
   - Token storage and refresh
   - Error handling for expired tokens

3. **Replace Simulation Code**
   - Update `_publish_post` method
   - Add media upload functionality
   - Implement proper error handling

4. **Add Media Handling**
   - Image upload and processing
   - Video upload with progress tracking
   - Media validation and optimization

5. **Testing and Validation**
   - Test with Instagram Business account
   - Validate different post types
   - Error handling and edge cases

## Environment Variables Required

```bash
# Instagram Graph API
INSTAGRAM_APP_ID=your_facebook_app_id
INSTAGRAM_APP_SECRET=your_facebook_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_USER_ID=your_instagram_business_user_id
INSTAGRAM_PAGE_ID=your_connected_facebook_page_id

# Optional: Webhook configuration
INSTAGRAM_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token
INSTAGRAM_WEBHOOK_URL=your_webhook_endpoint_url
```

## Alternative: Buffer API Integration

If Instagram Graph API setup is complex, Buffer API provides a simpler alternative:

```python
# Buffer API example
import requests

def publish_to_instagram_via_buffer(content, access_token, profile_id):
    url = "https://api.bufferapp.com/1/updates/create.json"
    data = {
        "text": content,
        "profile_ids[]": profile_id,
        "access_token": access_token
    }
    response = requests.post(url, data=data)
    return response.json()
```

## Next Steps

1. Choose between Instagram Graph API (direct) or Buffer API (third-party)
2. Set up required accounts and credentials
3. Implement authentication and token management
4. Replace simulation code with actual API calls
5. Test with real Instagram Business account
6. Add comprehensive error handling and logging

## Files to Modify

- `social_media_publisher/sub_agents/instagram.py`: Replace simulation with API calls
- `social_media_publisher/config.py`: Add Instagram API configuration
- `.env`: Add Instagram API credentials
- `requirements.txt`: Add required packages (requests, facebook-sdk)

## Security Considerations

- Store access tokens securely (encrypted)
- Implement token refresh mechanism
- Use HTTPS for all API calls
- Validate and sanitize all inputs
- Implement rate limiting
- Log security events and API errors