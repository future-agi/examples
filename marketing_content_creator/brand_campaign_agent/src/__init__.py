"""
Brand Campaign Agent - AI-powered brand campaign generation
"""

from .models import (
    CampaignBrief, ProductInfo, Demographics, CampaignObjective,
    PlatformType, CampaignOutput, GenerationConfig
)
from .campaign_orchestrator import CampaignOrchestrator
from .openai_client import CampaignGenerator, OpenAIClient
from .image_generator import ImageGenerator

__version__ = "1.0.0"
__author__ = "Brand Campaign Agent Team"
__description__ = "AI-powered comprehensive brand campaign generation using OpenAI"

__all__ = [
    "CampaignBrief",
    "ProductInfo", 
    "Demographics",
    "CampaignObjective",
    "PlatformType",
    "CampaignOutput",
    "GenerationConfig",
    "CampaignOrchestrator",
    "CampaignGenerator",
    "OpenAIClient",
    "ImageGenerator"
]

