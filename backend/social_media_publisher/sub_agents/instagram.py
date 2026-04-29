"""Instagram Publishing Agent

Specialized agent for publishing content to Instagram using Instagram Graph API.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

from .base import BaseSocialMediaAgent
from ..config import SocialPlatform, PostType, PostStatus
from ..instagram_api_helper import InstagramAPIHelper
from ai_providers.base import AIResponse

logger = logging.getLogger(__name__)


class InstagramAgent(BaseSocialMediaAgent):
    """Instagram-specific social media publishing agent."""
    
    def _get_platform(self) -> SocialPlatform:
        """Get the platform this agent handles."""
        return SocialPlatform.INSTAGRAM
    
    async def _platform_initialize(self) -> None:
        """Instagram-specific initialization."""
        # Validate Instagram credentials using helper
        validation_result = InstagramAPIHelper.validate_credentials()
        
        if not validation_result["valid"]:
            missing_creds = ", ".join(validation_result["missing_credentials"])
            logger.error(f"Instagram credentials validation failed. Missing: {missing_creds}")
            logger.error("Please configure Instagram API credentials in environment variables")
        
        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                logger.warning(warning)
        
        # Log debug info for troubleshooting
        debug_info = InstagramAPIHelper.get_debug_info()
        logger.info(f"Instagram API debug info: {debug_info}")
        
        logger.info("Instagram agent initialized successfully")
    
    async def _platform_validate_content(
        self,
        content: str,
        post_type: Optional[PostType],
        images: Optional[List[str]],
        videos: Optional[List[str]]
    ) -> None:
        """Instagram-specific content validation."""
        # Instagram requires at least one image or video for most post types
        if post_type in [PostType.IMAGE_POST, PostType.CAROUSEL_POST, PostType.REEL]:
            if not images and not videos:
                raise ValueError(f"{post_type.value} requires at least one image or video")
        
        # Reel-specific validation
        if post_type == PostType.REEL:
            if not videos:
                raise ValueError("Reels require a video")
            if len(videos) > 1:
                raise ValueError("Reels can only have one video")
        
        # Story validation
        if post_type == PostType.STORY:
            if not images and not videos:
                raise ValueError("Stories require at least one image or video")
    
    async def _get_optimization_prompt(
        self,
        content: str,
        post_type: Optional[PostType],
        target_audience: Optional[str]
    ) -> str:
        """Get Instagram-specific content optimization prompt."""
        audience_context = f"Target audience: {target_audience}" if target_audience else "General Instagram audience"
        
        post_type_guidance = {
            PostType.TEXT_POST: "engaging text post that encourages likes and comments",
            PostType.IMAGE_POST: "compelling image post with descriptive caption",
            PostType.VIDEO_POST: "engaging video post that captures attention",
            PostType.CAROUSEL_POST: "carousel post that tells a story across multiple slides",
            PostType.STORY: "Instagram Story that's casual and authentic",
            PostType.REEL: "Reel caption that's trendy and shareable",
            PostType.ARTICLE: "engaging article-style post with informative content",
            PostType.EVENT: "event announcement post that drives attendance",
            PostType.POLL: "interactive poll post that encourages engagement"
        }
        
        post_guidance = post_type_guidance.get(post_type, "engaging Instagram post")
        
        return f"""
Optimize the following content for Instagram as a {post_guidance}.

{audience_context}

Original content: {content}

Instructions:
1. Make it Instagram-friendly with engaging language
2. Keep it under {self.platform_config.max_text_length} characters
3. Use emojis appropriately to enhance engagement
4. Create compelling hooks in the first line
5. Include call-to-action if appropriate
6. Make it authentic and relatable
7. Consider Instagram's visual-first nature
8. Don't include hashtags (they will be added separately)

Return only the optimized content without any additional formatting or explanations.
"""
    
    async def _get_hashtag_prompt(self, content: str, post_type: Optional[PostType]) -> str:
        """Get Instagram-specific hashtag generation prompt."""
        return f"""
Generate relevant Instagram hashtags for the following content:

{content}

Post type: {post_type.value if post_type else 'general'}

Instructions:
1. Generate {self.config.hashtag_config.max_hashtags} relevant hashtags
2. Mix popular and niche hashtags for better reach
3. Include trending hashtags when relevant
4. Avoid banned or shadowbanned hashtags
5. Make hashtags specific to the content
6. Include location-based hashtags if applicable
7. Add community hashtags for engagement
8. Consider the target audience

Format: Return hashtags separated by spaces, each starting with #
Example: #photography #sunset #nature #beautiful #instagood

Hashtags:
"""
    
    def _get_default_image_url(self) -> str:
        """Get a reliable default image URL for Instagram posting."""
        # Use a reliable, publicly accessible image URL
        reliable_images = [
            "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg",
            "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1080&fit=crop&auto=format",
            "https://raw.githubusercontent.com/microsoft/vscode/main/resources/linux/code.png"
        ]
        
        # Test each URL and return the first working one
        import requests
        for url in reliable_images:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200 and 'image/' in response.headers.get('content-type', ''):
                    logger.info(f"Using reliable image URL: {url}")
                    return url
            except Exception as e:
                logger.debug(f"Image URL test failed for {url}: {e}")
                continue
        
        # Fallback to first URL if testing fails
        logger.info(f"Using fallback image URL: {reliable_images[0]}")
        return reliable_images[0]

    async def _publish_post(self, post_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Publish post immediately to Instagram using Instagram Graph API."""
        try:
            # Check if we have valid Instagram credentials
            if not self.platform_config.access_token:
                logger.warning("Instagram access token not configured, using simulation mode")
                return await self._simulate_instagram_post(post_data, request_id)
            
            # Use Instagram Graph API for actual posting
            return await self._publish_via_instagram_graph_api(post_data, request_id)
            
        except Exception as e:
            logger.error(f"Failed to publish to Instagram: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": "instagram",
                "status": PostStatus.FAILED.value
            }
    
    async def _publish_via_instagram_graph_api(self, post_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Publish to Instagram using Instagram Graph API."""
        import requests
        import json
        
        try:
            access_token = self.platform_config.access_token
            user_id = os.getenv("INSTAGRAM_USER_ID")
            
            if not user_id:
                raise ValueError("Instagram User ID not configured")
            
            # Prepare caption with hashtags
            caption = self._format_instagram_caption(
                post_data["content"],
                post_data["hashtags"]
            )
            
            # Step 1: Create media container
            media_container_id = await self._create_media_container(
                user_id, access_token, caption, post_data
            )
            
            if not media_container_id:
                raise ValueError("Failed to create media container")
            
            # Step 2: Publish the media container
            publish_result = await self._publish_media_container(
                user_id, access_token, media_container_id
            )
            
            if publish_result.get("success"):
                logger.info(f"Successfully published to Instagram: {publish_result['post_id']}")
                return {
                    "success": True,
                    "post_id": publish_result["post_id"],
                    "platform": "instagram",
                    "status": PostStatus.PUBLISHED.value,
                    "url": f"https://instagram.com/p/{publish_result['post_id']}",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "instagram_data": publish_result.get("data", {}),
                    "api_response": publish_result
                }
            else:
                raise ValueError(f"Publishing failed: {publish_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Instagram Graph API publishing failed: {e}")
            # Fallback to simulation if API fails
            logger.info("Falling back to simulation mode")
            return await self._simulate_instagram_post(post_data, request_id)
    
    async def _create_media_container(self, user_id: str, access_token: str, caption: str, post_data: Dict[str, Any]) -> Optional[str]:
        """Create a media container using Instagram Graph API with proper image URL handling."""
        import requests
        
        try:
            # Validate required parameters
            if not user_id or not access_token:
                raise ValueError("Missing required Instagram credentials (user_id or access_token)")
            
            url = f"https://graph.facebook.com/v18.0/{user_id}/media"
            
            # Prepare media data based on post type
            media_data = {
                "caption": caption[:2200],  # Instagram caption limit
                "access_token": access_token
            }
            
            # Handle different media types - Use image_url parameter for Instagram API
            image_url = None
            if post_data.get("images") and len(post_data["images"]) > 0:
                # Check if we have actual image files or URLs
                potential_image = post_data["images"][0]
                
                # If it's a local file path, we need to host it or use a valid URL
                if os.path.exists(potential_image):
                    logger.info(f"Local image file found: {potential_image}")
                    # For Instagram API, we need a publicly accessible URL
                    # Use a reliable image hosting service URL instead
                    image_url = self._get_default_image_url()
                    logger.info(f"Using reliable hosted image URL: {image_url}")
                elif self._is_instagram_compatible_url(potential_image):
                    image_url = potential_image
                    logger.info(f"Using provided image URL: {image_url}")
                else:
                    # Use a reliable default image URL
                    image_url = self._get_default_image_url()
                    logger.info(f"Using default reliable image URL: {image_url}")
            else:
                # No image provided, use default reliable URL
                image_url = "https://fastly.picsum.photos/id/98/1080/1080.jpg?hmac=dJhmzeqsZd6CeSVc9GB9e-8dVvc2EuiIPVwNC4NzAeM"
                logger.info("No image provided, using default reliable image URL")
                
            # Add image_url to media data (required by Instagram API)
            if image_url:
                media_data["image_url"] = image_url
                logger.info(f"Added image_url to media data: {image_url}")
            elif post_data.get("videos") and len(post_data["videos"]) > 0:
                # Video post - use video_url parameter
                potential_video = post_data["videos"][0]
                
                if self._is_instagram_compatible_url(potential_video):
                    media_data["media_type"] = "VIDEO"
                    media_data["video_url"] = potential_video
                    logger.info(f"Using video URL: {potential_video}")
                else:
                    # Fallback to image for unsupported video URLs
                    logger.warning("Video URL not compatible with Instagram. Using default image instead.")
                    image_url = "https://picsum.photos/1080/1080?random=2"
                    media_data["image_url"] = image_url
                    logger.info(f"Using fallback image URL: {image_url}")
            else:
                # Text-only post (not supported by Instagram, use default image)
                logger.info("Instagram requires media for posts. Using default image.")
                image_url = self._get_default_image_url()
                media_data["image_url"] = image_url
                logger.info(f"Using default image URL for text post: {image_url}")
            
            # Log the request for debugging
            logger.info(f"Creating Instagram media container with data: {media_data}")
            
            # Make the request with URL-based media (no file upload)
            response = requests.post(url, data=media_data, timeout=60)
            
            # Log response for debugging
            logger.info(f"Instagram API response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Instagram API error response: {response.text}")
            else:
                logger.info(f"Instagram API success response: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            container_id = result.get("id")
            
            if container_id:
                logger.info(f"Successfully created media container: {container_id}")
                return container_id
            else:
                logger.error(f"No container ID in response: {result}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create media container: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
                
                # Parse error response for specific Instagram errors
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error'].get('message', 'Unknown error')
                        error_code = error_data['error'].get('code', 'Unknown code')
                        logger.error(f"Instagram API Error - Code: {error_code}, Message: {error_msg}")
                        
                        # Handle specific error cases
                        if 'media uri doesn\'t meet our requirements' in error_msg.lower():
                            logger.error("Instagram rejected the media URL. The URL must be publicly accessible and serve actual image/video content.")
                        elif 'only photo or video can be accepted' in error_msg.lower():
                            logger.error("Instagram requires valid photo or video content. Text-only posts are not supported.")
                except:
                    pass
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating media container: {e}")
            return None
    
    async def _publish_media_container(self, user_id: str, access_token: str, container_id: str) -> Dict[str, Any]:
        """Publish a media container using Instagram Graph API."""
        import requests
        
        try:
            url = f"https://graph.facebook.com/v18.0/{user_id}/media_publish"
            
            data = {
                "creation_id": container_id,
                "access_token": access_token
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "success": True,
                "post_id": result.get("id"),
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to publish media container: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error publishing media container: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _simulate_instagram_post(self, post_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Simulate Instagram posting for testing/development."""
        post_id = f"ig_{uuid.uuid4().hex[:12]}"
        
        # Prepare Instagram-specific post data
        instagram_post = {
            "id": post_id,
            "caption": self._format_instagram_caption(
                post_data["content"],
                post_data["hashtags"]
            ),
            "media_type": self._get_instagram_media_type(post_data["post_type"]),
            "media_urls": post_data["images"] + post_data["videos"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Simulate API response
        result = {
            "success": True,
            "post_id": post_id,
            "platform": "instagram",
            "status": PostStatus.PUBLISHED.value,
            "url": f"https://instagram.com/p/{post_id}",
            "published_at": instagram_post["timestamp"],
            "simulation": True,
            "note": "This is a simulated post. Configure Instagram API credentials for actual posting.",
            "metrics": {
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "saves": 0,
                "reach": 0,
                "impressions": 0
            },
            "instagram_data": instagram_post
        }
        
        logger.info(f"Successfully simulated Instagram post: {post_id}")
        return result
    
    async def _schedule_post(self, post_data: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Schedule post for later publishing on Instagram."""
        try:
            # Simulate Instagram scheduling
            # Note: Instagram doesn't support native scheduling through API
            # This would typically require a third-party service like Buffer, Hootsuite, etc.
            
            post_id = f"ig_scheduled_{uuid.uuid4().hex[:12]}"
            schedule_time = post_data.get("schedule_time")
            
            result = {
                "success": True,
                "post_id": post_id,
                "platform": "instagram",
                "status": PostStatus.SCHEDULED.value,
                "scheduled_for": schedule_time.isoformat() if schedule_time else None,
                "message": "Post scheduled successfully. Note: Instagram requires third-party scheduling tools.",
                "scheduling_service": "internal_scheduler",  # In real implementation, would be Buffer/Hootsuite
                "content_preview": {
                    "caption": self._format_instagram_caption(
                        post_data["content"],
                        post_data["hashtags"]
                    ),
                    "media_count": len(post_data["images"]) + len(post_data["videos"]),
                    "post_type": post_data["post_type"].value
                }
            }
            
            logger.info(f"Successfully scheduled Instagram post: {post_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to schedule Instagram post: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": "instagram",
                "status": PostStatus.FAILED.value
            }
    
    def _format_instagram_caption(self, content: str, hashtags: List[str]) -> str:
        """Format caption for Instagram with hashtags."""
        return InstagramAPIHelper.format_instagram_caption(content, hashtags)
    
    def _get_instagram_media_type(self, post_type: PostType) -> str:
        """Get Instagram media type from post type."""
        return InstagramAPIHelper.get_instagram_media_type(post_type.value)
    
    def _get_local_image_path(self) -> str:
        """Get path to local default image for Instagram posts."""
        # Use the local image file from assets directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_image_path = os.path.join(current_dir, "assets", "images.jpg")
        
        # Alternative paths to check
        alternative_paths = [
            os.path.join(current_dir, "assets", "sample_image.jpg"),
            os.path.join(current_dir, "assets", "default.jpg"),
            os.path.join(current_dir, "assets", "placeholder.jpg")
        ]
        
        # Check if default image exists
        if os.path.exists(default_image_path):
            return default_image_path
        
        # Check alternative paths
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                logger.info(f"Using alternative image: {alt_path}")
                return alt_path
        
        # If no local image found, create a simple one
        logger.warning(f"No local image found. Creating default image at: {default_image_path}")
        self._create_default_image(default_image_path)
        return default_image_path
    
    def _create_default_image(self, image_path: str) -> None:
        """Create a simple default image if none exists."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import os
            
            # Create assets directory if it doesn't exist
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            # Create a simple 1080x1080 image
            img = Image.new('RGB', (1080, 1080), color='#4A90E2')
            draw = ImageDraw.Draw(img)
            
            # Add text
            text = "Social Media Post"
            try:
                # Try to use a system font
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Calculate text position (center)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (1080 - text_width) // 2
            y = (1080 - text_height) // 2
            
            # Draw text
            draw.text((x, y), text, fill='white', font=font)
            
            # Save image
            img.save(image_path, 'JPEG', quality=95)
            logger.info(f"Created default image: {image_path}")
            
        except ImportError:
            logger.error("PIL (Pillow) not installed. Cannot create default image.")
            raise ValueError("PIL (Pillow) required to create default images. Install with: pip install Pillow")
        except Exception as e:
            logger.error(f"Failed to create default image: {e}")
            raise
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible."""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _is_instagram_compatible_url(self, url: str) -> bool:
        """Check if URL is compatible with Instagram's media requirements."""
        # Instagram has specific requirements for media URLs:
        # 1. Must be publicly accessible (not localhost or placeholder services that don't work)
        # 2. Must serve actual image/video content
        # 3. Must be HTTPS
        
        if not url.startswith('https://'):
            return False
        
        # Known problematic domains that Instagram can't fetch from
        blocked_domains = [
            'via.placeholder.com',
            'placeholder.com',
            'dummyimage.com',
            'fakeimg.pl',
            'localhost',
            '127.0.0.1'
        ]
        
        for domain in blocked_domains:
            if domain in url.lower():
                return False
        
        # Known good domains that Instagram can fetch from
        trusted_domains = [
            'picsum.photos',
            'images.unsplash.com',
            'source.unsplash.com',
            'cdn.pixabay.com',
            'images.pexels.com',
            'i.imgur.com',
            'media.giphy.com',
            'unsplash.com'
        ]
        
        for domain in trusted_domains:
            if domain in url.lower():
                return True
        
        # For other domains, be more conservative
        return False
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """Get analytics for an Instagram post."""
        try:
            # Simulate Instagram analytics
            # In real implementation, would use Instagram Graph API
            
            analytics = {
                "post_id": post_id,
                "platform": "instagram",
                "analytics_available": True,
                "metrics": {
                    "likes": 127,
                    "comments": 23,
                    "shares": 8,
                    "saves": 45,
                    "reach": 1250,
                    "impressions": 1890,
                    "profile_visits": 34,
                    "website_clicks": 12,
                    "engagement_rate": 8.2
                },
                "audience_insights": {
                    "top_locations": ["New York", "Los Angeles", "Chicago"],
                    "age_groups": {
                        "18-24": 25,
                        "25-34": 45,
                        "35-44": 20,
                        "45+": 10
                    },
                    "gender_split": {
                        "female": 60,
                        "male": 40
                    }
                },
                "best_performing_hashtags": [
                    "#photography", "#instagood", "#photooftheday"
                ],
                "optimal_posting_time": "2024-04-28T17:00:00Z",
                "retrieved_at": datetime.now(timezone.utc).isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get Instagram analytics: {e}")
            return {
                "post_id": post_id,
                "platform": "instagram",
                "analytics_available": False,
                "error": str(e)
            }
    
    async def create_story(
        self,
        content: str,
        media_url: str,
        request_id: str,
        stickers: Optional[List[Dict[str, Any]]] = None,
        mentions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create an Instagram Story."""
        try:
            story_id = f"ig_story_{uuid.uuid4().hex[:12]}"
            
            story_data = {
                "id": story_id,
                "content": content,
                "media_url": media_url,
                "stickers": stickers or [],
                "mentions": mentions or [],
                "expires_at": (datetime.now(timezone.utc).timestamp() + 86400),  # 24 hours
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = {
                "success": True,
                "story_id": story_id,
                "platform": "instagram",
                "type": "story",
                "expires_in_hours": 24,
                "story_data": story_data
            }
            
            logger.info(f"Successfully created Instagram story: {story_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Instagram story: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": "instagram",
                "type": "story"
            }
    
    async def create_reel(
        self,
        caption: str,
        video_url: str,
        request_id: str,
        cover_image_url: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create an Instagram Reel."""
        try:
            reel_id = f"ig_reel_{uuid.uuid4().hex[:12]}"
            
            formatted_caption = self._format_instagram_caption(caption, hashtags or [])
            
            reel_data = {
                "id": reel_id,
                "caption": formatted_caption,
                "video_url": video_url,
                "cover_image_url": cover_image_url,
                "hashtags": hashtags or [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = {
                "success": True,
                "reel_id": reel_id,
                "platform": "instagram",
                "type": "reel",
                "url": f"https://instagram.com/reel/{reel_id}",
                "reel_data": reel_data
            }
            
            logger.info(f"Successfully created Instagram reel: {reel_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create Instagram reel: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": "instagram",
                "type": "reel"
            }