# Instagram API Debug Guide

## Current Issue Analysis

Based on your logs, the Instagram Graph API is failing with error code 9004:

```
Only photo or video can be accepted as media type.
Media download has failed. The media URI doesn't meet our requirements.
The media could not be fetched from this URI: https://picsum.photos/1080/1080?random=1
```

## Root Causes

1. **Image URL Requirements**: Instagram Graph API requires:
   - Publicly accessible HTTPS URLs
   - Direct links to actual image files (JPEG, PNG)
   - URLs that return proper image content-type headers
   - No redirects or dynamic image generation services

2. **Picsum Photos Issue**: The service `https://picsum.photos/` uses redirects and dynamic generation, which Instagram API rejects.

## Sample cURL Commands for Testing

### 1. Test Instagram Access Token
```bash
curl -X GET \
  "https://graph.facebook.com/v18.0/me?access_token=YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 2. Get Instagram Business Account ID
```bash
curl -X GET \
  "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 3. Create Media Container (Step 1)
```bash
curl -X POST \
  "https://graph.facebook.com/v18.0/YOUR_IG_USER_ID/media" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/your-image.jpg",
    "caption": "Your caption here #hashtag",
    "access_token": "YOUR_ACCESS_TOKEN"
  }'
```

### 4. Publish Media Container (Step 2)
```bash
curl -X POST \
  "https://graph.facebook.com/v18.0/YOUR_IG_USER_ID/media_publish" \
  -H "Content-Type: application/json" \
  -d '{
    "creation_id": "MEDIA_CONTAINER_ID_FROM_STEP_1",
    "access_token": "YOUR_ACCESS_TOKEN"
  }'
```

## Valid Image URL Examples

### Working Image URLs:
```
https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1080&fit=crop
https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg
https://your-domain.com/static/images/sample.jpg
```

### Non-Working URLs:
```
https://picsum.photos/1080/1080?random=1  # Uses redirects
https://via.placeholder.com/1080x1080     # Blocked by Instagram
https://dummyimage.com/1080x1080          # Dynamic generation
```

## Testing Strategy

### 1. Manual cURL Test
Use the cURL commands above with a valid image URL to test if your Instagram API setup works.

### 2. Image URL Validation
Test if an image URL works with Instagram:
```bash
curl -I "https://your-image-url.jpg"
```
Should return:
- Status: 200 OK
- Content-Type: image/jpeg or image/png
- No redirects (301/302)

### 3. Debug Your Access Token
```bash
curl "https://graph.facebook.com/debug_token?input_token=YOUR_ACCESS_TOKEN&access_token=YOUR_APP_ACCESS_TOKEN"
```

## Environment Variables Needed

```env
# Instagram API Configuration
INSTAGRAM_ACCESS_TOKEN=your_long_lived_access_token
INSTAGRAM_USER_ID=your_instagram_business_account_id
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
```

## Common Issues and Solutions

### Issue 1: Invalid Access Token
**Error**: `(#190) Invalid OAuth access token`
**Solution**: Generate a new long-lived access token

### Issue 2: Media Download Failed
**Error**: `Media download has failed. The media URI doesn't meet our requirements`
**Solution**: Use direct image URLs, not dynamic services

### Issue 3: Insufficient Permissions
**Error**: `(#200) Requires business verification`
**Solution**: Complete Instagram Business verification

### Issue 4: Rate Limiting
**Error**: `(#4) Application request limit reached`
**Solution**: Implement rate limiting and retry logic

## Recommended Image Hosting Solutions

1. **AWS S3**: Host images on S3 with public read access
2. **Cloudinary**: Image hosting service with direct URLs
3. **Your Own Server**: Host images on your domain
4. **GitHub Raw**: For testing, use raw GitHub URLs

## Next Steps

1. Test with cURL commands using a valid image URL
2. Verify your Instagram Business Account setup
3. Update the code to use proper image URLs
4. Implement proper error handling and logging
