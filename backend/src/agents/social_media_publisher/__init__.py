"""Social Media Publisher Agent Package

A comprehensive social media publishing system with specialized sub-agents
for different platforms (Instagram, LinkedIn, Facebook).
"""

from .main_agent import SocialMediaPublisherMainAgent
from .factory import SocialMediaAgentFactory
from .config import (
    SocialMediaPublisherConfig,
    SocialPlatform,
    PostType,
    PostScheduling,
    DEFAULT_CONFIG
)

__version__ = "1.0.0"
__all__ = [
    "SocialMediaPublisherMainAgent",
    "SocialMediaAgentFactory", 
    "SocialMediaPublisherConfig",
    "SocialPlatform",
    "PostType",
    "PostScheduling",
    "DEFAULT_CONFIG"
]