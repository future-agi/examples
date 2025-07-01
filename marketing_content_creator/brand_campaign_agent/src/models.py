"""
Data models for the Brand Campaign Agent
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CampaignObjective(str, Enum):
    AWARENESS = "awareness"
    CONVERSION = "conversion"
    RETENTION = "retention"
    ENGAGEMENT = "engagement"


class PlatformType(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    GOOGLE_ADS = "google_ads"
    PRINT = "print"
    EMAIL = "email"
    WEBSITE = "website"


class Demographics(BaseModel):
    """Target demographic information"""
    age_range: tuple[int, int] = Field(description="Age range (min, max)")
    gender_distribution: Dict[str, float] = Field(
        description="Gender distribution as percentages",
        default={"male": 50.0, "female": 50.0}
    )
    income_level: str = Field(description="Income bracket (low, medium, high, luxury)")
    geographic_location: List[str] = Field(description="Target locations/regions")
    education_level: str = Field(description="Primary education level")
    interests: List[str] = Field(description="Key interests and hobbies", default=[])
    values: List[str] = Field(description="Core values and beliefs", default=[])


class ProductInfo(BaseModel):
    """Product or service information"""
    name: str = Field(description="Product/service name")
    category: str = Field(description="Product category")
    description: str = Field(description="Detailed product description")
    key_features: List[str] = Field(description="Main features and benefits")
    price_point: str = Field(description="Price positioning (budget, mid-range, premium, luxury)")
    unique_selling_propositions: List[str] = Field(description="What makes it unique")
    competitors: List[str] = Field(description="Main competitors", default=[])


class CampaignBrief(BaseModel):
    """Complete campaign brief input"""
    product_info: ProductInfo
    demographics: Demographics
    objectives: List[CampaignObjective]
    platforms: List[PlatformType]
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    brand_guidelines: Optional[Dict[str, Any]] = None
    additional_context: Optional[str] = None


class ColorPalette(BaseModel):
    """Brand color palette"""
    primary: str = Field(description="Primary brand color (hex)")
    secondary: str = Field(description="Secondary brand color (hex)")
    accent: str = Field(description="Accent color (hex)")
    neutral: str = Field(description="Neutral color (hex)")
    background: str = Field(description="Background color (hex)")
    text: str = Field(description="Text color (hex)")
    psychology: str = Field(description="Color psychology explanation")


class TypographyGuide(BaseModel):
    """Typography recommendations"""
    primary_font: str = Field(description="Primary font family")
    secondary_font: str = Field(description="Secondary font family")
    heading_style: str = Field(description="Heading typography style")
    body_style: str = Field(description="Body text typography style")
    font_pairing_rationale: str = Field(description="Why these fonts work together")


class TextContent(BaseModel):
    """Generated text content"""
    headlines: List[str] = Field(description="Campaign headlines")
    taglines: List[str] = Field(description="Brand taglines")
    ad_copy: Dict[str, List[str]] = Field(description="Ad copy by platform")
    product_descriptions: List[str] = Field(description="Product descriptions")
    call_to_actions: List[str] = Field(description="Call-to-action phrases")
    social_media_posts: Dict[str, List[str]] = Field(description="Social media content by platform")


class VisualAsset(BaseModel):
    """Visual asset information"""
    filename: str = Field(description="Asset filename")
    asset_type: str = Field(description="Type of visual asset")
    description: str = Field(description="Asset description")
    dimensions: tuple[int, int] = Field(description="Width x Height")
    platform_optimized: List[PlatformType] = Field(description="Optimized for platforms")


class BrandElements(BaseModel):
    """Brand design elements"""
    color_palette: ColorPalette
    typography: TypographyGuide
    logo_concepts: List[str] = Field(description="Logo concept descriptions")
    visual_style: str = Field(description="Overall visual style description")
    brand_personality: str = Field(description="Brand personality description")


class CampaignOutput(BaseModel):
    """Complete campaign output"""
    campaign_id: str = Field(description="Unique campaign identifier")
    brief: CampaignBrief = Field(description="Original campaign brief")
    text_content: TextContent = Field(description="Generated text content")
    visual_assets: List[VisualAsset] = Field(description="Generated visual assets")
    brand_elements: BrandElements = Field(description="Brand design elements")
    campaign_summary: str = Field(description="Executive summary of the campaign")
    recommendations: List[str] = Field(description="Implementation recommendations")
    created_at: str = Field(description="Creation timestamp")


class GenerationConfig(BaseModel):
    """Configuration for content generation"""
    openai_api_key: str
    model_text: str = "gpt-4o"
    model_image: str = "gpt-image-1"
    max_tokens: int = 2000
    temperature: float = 0.7
    image_size: str = "1024x1024"
    image_quality: str = "standard"
    output_directory: str = "./output"
    enable_image_generation: bool = True
    enable_brand_analysis: bool = True
    max_headlines: int = 5
    max_taglines: int = 3
    max_ad_copy_variants: int = 3

