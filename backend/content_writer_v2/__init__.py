"""Content Writer v2 - Modular Content Generation System

A comprehensive content generation system with specialized sub-agents
for different content types and use cases.
"""

from .main_agent import ContentWriterMainAgent
from .sub_agents import (
    SocialMediaAgent,
    BlogAgent,
    ScriptAgent,
    MarketingCopyAgent,
    TechnicalWritingAgent
)
from .config import ContentWriterV2Config
from .factory import ContentAgentFactory

__version__ = "2.0.0"
__all__ = [
    "ContentWriterMainAgent",
    "SocialMediaAgent",
    "BlogAgent", 
    "ScriptAgent",
    "MarketingCopyAgent",
    "TechnicalWritingAgent",
    "ContentWriterV2Config",
    "ContentAgentFactory"
]