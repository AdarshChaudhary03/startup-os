"""Instagram API Helper Functions

Utility functions for Instagram API integration and debugging.
"""

import os
import re
import logging
import urllib.parse
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class InstagramAPIHelper:
    """Helper class for Instagram API operations."""
    
    @staticmethod
    def validate_credentials() -> Dict[str, Any]:
        """Validate Instagram API credentials."""
        validation_result = {
            "valid": True,
            "missing_credentials": [],
            "warnings": []
        }
        
        required_credentials = [
            "INSTAGRAM_ACCESS_TOKEN",
            "INSTAGRAM_USER_ID",
            "INSTAGRAM_APP_ID",
            "GROQ_API_KEY"
        ]
        
        for credential in required_credentials:
            if not os.getenv(credential):
                validation_result["missing_credentials"].append(credential)
                validation_result["valid"] = False
        
        # Check optional credentials
        if not os.getenv("INSTAGRAM_APP_SECRET"):
            validation_result["warnings"].append("INSTAGRAM_APP_SECRET not set (optional but recommended)")
        
        return validation_result
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate if a URL is properly formatted."""
        if not url or not isinstance(url, str):
            return False
            
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(url_pattern, url) is not None
    
    @staticmethod
    def generate_text_image_url(text: str, width: int = 1080, height: int = 1080) -> str:
        """Generate a text image URL for Instagram posts without media."""
        # Sanitize and limit text length
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)[:50]
        encoded_text = urllib.parse.quote(clean_text)
        
        # Use a placeholder service (in production, use a proper image generation service)
        return f"https://via.placeholder.com/{width}x{height}/4267B2/FFFFFF?text={encoded_text}"
    
    @staticmethod
    def format_instagram_caption(content: str, hashtags: list = None) -> str:
        """Format caption for Instagram with proper length and hashtags."""
        # Instagram caption limit is 2200 characters
        max_caption_length = 2200
        
        caption = content.strip()
        
        if hashtags:
            # Format hashtags
            formatted_hashtags = []
            for tag in hashtags:
                if isinstance(tag, str):
                    clean_tag = tag.strip().replace('#', '')
                    if clean_tag:
                        formatted_hashtags.append(f"#{clean_tag}")
            
            if formatted_hashtags:
                hashtag_string = " ".join(formatted_hashtags)
                
                # Check if adding hashtags exceeds limit
                if len(caption) + len(hashtag_string) + 2 <= max_caption_length:  # +2 for \n\n
                    caption += f"\n\n{hashtag_string}"
                else:
                    # Truncate caption to fit hashtags
                    available_space = max_caption_length - len(hashtag_string) - 2
                    if available_space > 50:  # Minimum meaningful caption length
                        caption = caption[:available_space].strip() + f"\n\n{hashtag_string}"
                    else:
                        # If hashtags are too long, truncate them
                        caption = caption[:max_caption_length]
        else:
            # No hashtags, just ensure caption doesn't exceed limit
            caption = caption[:max_caption_length]
        
        return caption
    
    @staticmethod
    def get_instagram_media_type(post_type_value: str) -> str:
        """Get Instagram media type from post type value."""
        type_mapping = {
            "text_post": "IMAGE",  # Instagram doesn't support text-only posts
            "image_post": "IMAGE",
            "video_post": "VIDEO",
            "carousel_post": "CAROUSEL_ALBUM",
            "story": "STORY",
            "reel": "REEL"
        }
        return type_mapping.get(post_type_value.lower(), "IMAGE")
    
    @staticmethod
    def prepare_media_data(post_data: Dict[str, Any], caption: str, access_token: str) -> Dict[str, Any]:
        """Prepare media data for Instagram API request."""
        media_data = {
            "caption": caption,
            "access_token": access_token
        }
        
        # Handle different media types
        if post_data.get("images") and len(post_data["images"]) > 0:
            # Single image post
            image_url = post_data["images"][0]
            if InstagramAPIHelper.is_valid_url(image_url):
                media_data["image_url"] = image_url
            else:
                raise ValueError(f"Invalid image URL: {image_url}")
                
        elif post_data.get("videos") and len(post_data["videos"]) > 0:
            # Video post
            video_url = post_data["videos"][0]
            if InstagramAPIHelper.is_valid_url(video_url):
                media_data["media_type"] = "VIDEO"
                media_data["video_url"] = video_url
            else:
                raise ValueError(f"Invalid video URL: {video_url}")
                
        else:
            # Text-only post (generate text image)
            logger.warning("Instagram requires media for posts. Generating text image.")
            text_image_url = InstagramAPIHelper.generate_text_image_url(caption)
            media_data["image_url"] = text_image_url
        
        return media_data
    
    @staticmethod
    def debug_api_response(response, operation: str = "API call"):
        """Debug Instagram API response."""
        logger.info(f"Instagram {operation} - Status: {response.status_code}")
        
        try:
            response_data = response.json()
            logger.info(f"Instagram {operation} - Response: {response_data}")
            
            # Check for specific error types
            if "error" in response_data:
                error_info = response_data["error"]
                error_code = error_info.get("code", "Unknown")
                error_message = error_info.get("message", "Unknown error")
                error_type = error_info.get("type", "Unknown")
                
                logger.error(f"Instagram API Error - Code: {error_code}, Type: {error_type}, Message: {error_message}")
                
                # Provide specific guidance for common errors
                if error_code == 100:
                    logger.error("Invalid parameter error. Check your request parameters.")
                elif error_code == 190:
                    logger.error("Access token error. Check your Instagram access token.")
                elif error_code == 200:
                    logger.error("Permission error. Check your app permissions.")
                    
        except Exception as e:
            logger.error(f"Could not parse Instagram API response: {e}")
            logger.error(f"Raw response: {response.text}")
    
    @staticmethod
    def get_debug_info() -> Dict[str, Any]:
        """Get debug information for Instagram API setup."""
        debug_info = {
            "timestamp": str(os.times()),
            "environment_variables": {},
            "api_endpoints": {
                "media_creation": "https://graph.facebook.com/v18.0/{user_id}/media",
                "media_publish": "https://graph.facebook.com/v18.0/{user_id}/media_publish",
                "user_info": "https://graph.facebook.com/v18.0/{user_id}"
            },
            "required_permissions": [
                "instagram_basic",
                "instagram_content_publish",
                "pages_read_engagement",
                "pages_show_list"
            ]
        }
        
        # Check environment variables (without exposing sensitive data)
        env_vars = [
            "INSTAGRAM_ACCESS_TOKEN",
            "INSTAGRAM_USER_ID",
            "INSTAGRAM_APP_ID",
            "GROQ_API_KEY",
            "SOCIAL_MEDIA_AI_MODEL"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive data
                if "TOKEN" in var or "SECRET" in var or "KEY" in var:
                    debug_info["environment_variables"][var] = f"{value[:8]}...{value[-4:]}"
                else:
                    debug_info["environment_variables"][var] = value
            else:
                debug_info["environment_variables"][var] = "NOT_SET"
        
        return debug_info
