# Instagram API Setup Guide

## Overview

This guide walks you through setting up Instagram Graph API integration for the Social Media Publisher Agent. After completing this setup, you'll be able to publish content directly to Instagram instead of using simulation mode.

## Prerequisites

1. **Instagram Business Account**: You need an Instagram Business account (not personal)
2. **Facebook Page**: The Instagram Business account must be connected to a Facebook Page
3. **Facebook Developer Account**: Access to Facebook Developers platform
4. **HTTPS Endpoint**: For webhook configuration (optional but recommended)

## Step-by-Step Setup

### 1. Convert Instagram to Business Account

1. Open Instagram mobile app
2. Go to Profile → Settings → Account
3. Select "Switch to Professional Account"
4. Choose "Business" account type
5. Connect to an existing Facebook Page or create a new one

### 2. Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "Create App"
3. Select "Business" as app type
4. Fill in app details:
   - App Name: "Your App Name"
   - App Contact Email: your email
   - Business Account: select your business account

### 3. Add Instagram Graph API Product

1. In your Facebook App dashboard
2. Click "Add Product"
3. Find "Instagram Graph API" and click "Set Up"
4. Complete the setup process

### 4. Configure App Permissions

1. Go to App Review → Permissions and Features
2. Request the following permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`

### 5. Generate Access Tokens

#### Option A: Using Graph API Explorer

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Select permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`
4. Click "Generate Access Token"
5. Copy the generated token

#### Option B: Using OAuth Flow (Recommended for Production)

```python
# Example OAuth flow implementation
import requests

def get_instagram_access_token(app_id, app_secret, redirect_uri, authorization_code):
    # Exchange authorization code for access token
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": authorization_code
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

### 6. Get Instagram Business User ID

```bash
# Using curl to get Instagram Business User ID
curl -X GET \
  "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_ACCESS_TOKEN"

# Then get Instagram account connected to the page
curl -X GET \
  "https://graph.facebook.com/v18.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_ACCESS_TOKEN"
```

### 7. Configure Environment Variables

Create a `.env` file in your backend directory:

```bash
# Instagram Graph API Configuration
INSTAGRAM_APP_ID=your_facebook_app_id
INSTAGRAM_APP_SECRET=your_facebook_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_USER_ID=your_instagram_business_user_id
INSTAGRAM_PAGE_ID=your_connected_facebook_page_id

# Optional settings
INSTAGRAM_API_VERSION=v18.0
INSTAGRAM_SIMULATION_MODE=false
```

### 8. Test the Integration

Run the test script to verify everything is working:

```bash
cd /path/to/your/project
python test_instagram_api.py
```

## API Endpoints Used

### Publishing Content

1. **Create Media Container**
   ```
   POST https://graph.facebook.com/v18.0/{ig-user-id}/media
   ```

2. **Publish Media Container**
   ```
   POST https://graph.facebook.com/v18.0/{ig-user-id}/media_publish
   ```

### Getting Analytics

```
GET https://graph.facebook.com/v18.0/{ig-media-id}/insights
```

## Rate Limits

- **Instagram Graph API**: 200 requests per hour per user
- **Publishing**: 25 posts per day per user
- **Stories**: 100 stories per day per user

## Troubleshooting

### Common Issues

1. **"Invalid Access Token"**
   - Check if token is expired
   - Verify token permissions
   - Regenerate token if needed

2. **"Instagram Account Not Found"**
   - Ensure Instagram account is Business type
   - Verify Instagram account is connected to Facebook Page
   - Check if Instagram User ID is correct

3. **"Media Upload Failed"**
   - Verify image/video format is supported
   - Check file size limits
   - Ensure media URL is accessible

4. **"Publishing Failed"**
   - Check if media container was created successfully
   - Verify publishing permissions
   - Ensure content meets Instagram guidelines

### Debug Mode

Enable debug logging to see detailed API responses:

```python
import logging
logging.getLogger('social_media_publisher').setLevel(logging.DEBUG)
```

### Simulation Mode

If you want to test without actual posting, set:

```bash
INSTAGRAM_SIMULATION_MODE=true
```

## Security Best Practices

1. **Token Security**
   - Store access tokens securely (encrypted)
   - Use environment variables, never hardcode
   - Implement token refresh mechanism
   - Monitor for token expiration

2. **API Security**
   - Use HTTPS for all API calls
   - Validate all inputs
   - Implement rate limiting
   - Log security events

3. **Content Validation**
   - Validate media formats and sizes
   - Check content for policy compliance
   - Implement content moderation
   - Handle API errors gracefully

## Production Deployment

1. **Environment Configuration**
   - Use secure secret management
   - Configure proper logging
   - Set up monitoring and alerts
   - Implement health checks

2. **Scaling Considerations**
   - Implement queue system for publishing
   - Handle rate limits gracefully
   - Use connection pooling
   - Monitor API usage

3. **Monitoring**
   - Track publishing success rates
   - Monitor API response times
   - Set up error alerting
   - Log all API interactions

## Support and Resources

- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api/)
- [Facebook App Review Process](https://developers.facebook.com/docs/app-review/)
- [Instagram Publishing Guidelines](https://developers.facebook.com/docs/instagram-api/guides/content-publishing/)
- [Rate Limiting Guide](https://developers.facebook.com/docs/graph-api/overview/rate-limiting/)

For additional support, check the logs in `logs/social_media_publisher.log` or enable debug mode for detailed API responses.
