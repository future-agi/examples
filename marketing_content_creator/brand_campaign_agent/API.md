# API Documentation - Brand Campaign Agent

This document provides comprehensive API documentation for integrating the Brand Campaign Agent into your applications.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
- [Data Models](#data-models)
- [Configuration](#configuration)
- [Examples](#examples)
- [Error Handling](#error-handling)

## Quick Start

```python
from src import CampaignOrchestrator, GenerationConfig, CampaignBrief, ProductInfo, Demographics

# 1. Configure the agent
config = GenerationConfig(
    openai_api_key="your-openai-api-key",
    output_directory="./campaigns",
    enable_image_generation=True
)

# 2. Create campaign orchestrator
orchestrator = CampaignOrchestrator(config)

# 3. Define campaign brief
brief = CampaignBrief(
    product_info=ProductInfo(
        name="EcoSmart Bottle",
        category="sustainable product",
        description="Smart water bottle made from recycled materials",
        key_features=["Smart tracking", "Eco-friendly", "Temperature control"],
        price_point="premium",
        unique_selling_propositions=["100% recycled", "AI-powered hydration"]
    ),
    demographics=Demographics(
        age_range=(25, 45),
        income_level="high",
        geographic_location=["United States"],
        education_level="college",
        interests=["sustainability", "health"],
        values=["environmental responsibility"]
    ),
    objectives=["awareness", "conversion"],
    platforms=["instagram", "facebook", "website"]
)

# 4. Generate campaign
campaign = orchestrator.generate_complete_campaign(brief)

# 5. Access results
print(f"Campaign ID: {campaign.campaign_id}")
print(f"Headlines: {campaign.text_content.headlines}")
print(f"Color Palette: {campaign.brand_elements.color_palette.primary}")
```

## Core Classes

### CampaignOrchestrator

Main class for coordinating campaign generation.

```python
class CampaignOrchestrator:
    def __init__(self, config: GenerationConfig)
    def generate_complete_campaign(self, brief: CampaignBrief) -> CampaignOutput
```

**Methods:**

#### `generate_complete_campaign(brief: CampaignBrief) -> CampaignOutput`

Generates a complete brand campaign including text content, visual assets, and brand elements.

**Parameters:**
- `brief` (CampaignBrief): Complete campaign brief with product info, demographics, and objectives

**Returns:**
- `CampaignOutput`: Complete campaign data including all generated content

**Example:**
```python
campaign = orchestrator.generate_complete_campaign(brief)
```

### CampaignGenerator

Handles text content generation using OpenAI GPT models.

```python
class CampaignGenerator:
    def __init__(self, config: GenerationConfig)
    def generate_headlines(self, brief: CampaignBrief) -> List[str]
    def generate_taglines(self, brief: CampaignBrief) -> List[str]
    def generate_ad_copy(self, brief: CampaignBrief) -> Dict[str, List[str]]
    def generate_color_palette(self, brief: CampaignBrief) -> ColorPalette
    def generate_typography_guide(self, brief: CampaignBrief) -> TypographyGuide
```

**Methods:**

#### `generate_headlines(brief: CampaignBrief) -> List[str]`
Generates campaign headlines based on the brief.

#### `generate_taglines(brief: CampaignBrief) -> List[str]`
Generates brand taglines.

#### `generate_ad_copy(brief: CampaignBrief) -> Dict[str, List[str]]`
Generates platform-specific ad copy.

### ImageGenerator

Handles visual asset creation using DALL-E.

```python
class ImageGenerator:
    def __init__(self, config: GenerationConfig)
    def generate_hero_images(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]
    def generate_social_media_assets(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]
    def generate_product_mockups(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]
```

## Data Models

### CampaignBrief

Main input model for campaign generation.

```python
class CampaignBrief(BaseModel):
    product_info: ProductInfo
    demographics: Demographics
    objectives: List[CampaignObjective]
    platforms: List[PlatformType]
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    additional_context: Optional[str] = None
```

### ProductInfo

Product or service information.

```python
class ProductInfo(BaseModel):
    name: str
    category: str
    description: str
    key_features: List[str]
    price_point: str  # "budget", "mid-range", "premium", "luxury"
    unique_selling_propositions: List[str]
    competitors: List[str] = []
```

### Demographics

Target audience demographics.

```python
class Demographics(BaseModel):
    age_range: tuple[int, int]
    gender_distribution: Dict[str, float] = {"male": 50.0, "female": 50.0}
    income_level: str  # "low", "medium", "high", "luxury"
    geographic_location: List[str]
    education_level: str  # "high-school", "college", "graduate", "mixed"
    interests: List[str] = []
    values: List[str] = []
```

### CampaignOutput

Complete campaign output model.

```python
class CampaignOutput(BaseModel):
    campaign_id: str
    brief: CampaignBrief
    text_content: TextContent
    visual_assets: List[VisualAsset]
    brand_elements: BrandElements
    campaign_summary: str
    recommendations: List[str]
    created_at: str
```

### TextContent

Generated text content.

```python
class TextContent(BaseModel):
    headlines: List[str]
    taglines: List[str]
    ad_copy: Dict[str, List[str]]  # Platform -> Copy variants
    product_descriptions: List[str]
    call_to_actions: List[str]
    social_media_posts: Dict[str, List[str]]  # Platform -> Posts
```

### BrandElements

Brand design elements.

```python
class BrandElements(BaseModel):
    color_palette: ColorPalette
    typography: TypographyGuide
    logo_concepts: List[str]
    visual_style: str
    brand_personality: str
```

### ColorPalette

Brand color palette with psychology.

```python
class ColorPalette(BaseModel):
    primary: str      # Hex color
    secondary: str    # Hex color
    accent: str       # Hex color
    neutral: str      # Hex color
    background: str   # Hex color
    text: str         # Hex color
    psychology: str   # Color psychology explanation
```

## Configuration

### GenerationConfig

Main configuration class.

```python
class GenerationConfig(BaseModel):
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
```

**Configuration Options:**

- `openai_api_key`: Your OpenAI API key
- `model_text`: GPT model for text generation ("gpt-4o", "gpt-3.5-turbo")
- `model_image`: DALL-E model for images ("gpt-image-1", "dall-e-2")
- `temperature`: Creativity level (0.0-1.0)
- `enable_image_generation`: Enable/disable image generation
- `max_headlines`: Number of headlines to generate
- `output_directory`: Where to save generated campaigns

## Examples

### Basic Campaign Generation

```python
from src import *

# Minimal configuration
config = GenerationConfig(openai_api_key="your-key")
orchestrator = CampaignOrchestrator(config)

# Simple brief
brief = CampaignBrief(
    product_info=ProductInfo(
        name="MyProduct",
        category="technology",
        description="An innovative tech product",
        key_features=["Feature 1", "Feature 2"],
        price_point="mid-range",
        unique_selling_propositions=["Unique benefit"]
    ),
    demographics=Demographics(
        age_range=(25, 45),
        income_level="medium",
        geographic_location=["US"],
        education_level="college"
    ),
    objectives=["awareness"],
    platforms=["facebook"]
)

# Generate campaign
campaign = orchestrator.generate_complete_campaign(brief)
```

### Text-Only Generation

```python
# Disable image generation for faster/cheaper generation
config = GenerationConfig(
    openai_api_key="your-key",
    enable_image_generation=False
)

orchestrator = CampaignOrchestrator(config)
campaign = orchestrator.generate_complete_campaign(brief)

# Access text content
headlines = campaign.text_content.headlines
taglines = campaign.text_content.taglines
ad_copy = campaign.text_content.ad_copy
```

### Custom Output Directory

```python
import os
from datetime import datetime

# Create timestamped output directory
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"./campaigns/{timestamp}"

config = GenerationConfig(
    openai_api_key="your-key",
    output_directory=output_dir
)

orchestrator = CampaignOrchestrator(config)
campaign = orchestrator.generate_complete_campaign(brief)

print(f"Campaign saved to: {output_dir}")
```

### Accessing Brand Elements

```python
campaign = orchestrator.generate_complete_campaign(brief)

# Color palette
colors = campaign.brand_elements.color_palette
print(f"Primary color: {colors.primary}")
print(f"Secondary color: {colors.secondary}")
print(f"Color psychology: {colors.psychology}")

# Typography
typography = campaign.brand_elements.typography
print(f"Primary font: {typography.primary_font}")
print(f"Font rationale: {typography.font_pairing_rationale}")

# Logo concepts
for i, concept in enumerate(campaign.brand_elements.logo_concepts):
    print(f"Logo concept {i+1}: {concept}")
```

### Platform-Specific Content

```python
# Generate content for specific platforms
brief.platforms = ["instagram", "linkedin", "email"]
campaign = orchestrator.generate_complete_campaign(brief)

# Access platform-specific ad copy
instagram_copy = campaign.text_content.ad_copy.get("instagram", [])
linkedin_copy = campaign.text_content.ad_copy.get("linkedin", [])

# Access social media posts
instagram_posts = campaign.text_content.social_media_posts.get("instagram", [])
```

### Batch Processing

```python
def generate_multiple_campaigns(briefs: List[CampaignBrief]) -> List[CampaignOutput]:
    """Generate multiple campaigns in batch"""
    config = GenerationConfig(openai_api_key="your-key")
    orchestrator = CampaignOrchestrator(config)
    
    campaigns = []
    for brief in briefs:
        try:
            campaign = orchestrator.generate_complete_campaign(brief)
            campaigns.append(campaign)
        except Exception as e:
            print(f"Failed to generate campaign for {brief.product_info.name}: {e}")
    
    return campaigns

# Use with multiple briefs
briefs = [brief1, brief2, brief3]
campaigns = generate_multiple_campaigns(briefs)
```

## Error Handling

### Common Exceptions

```python
from src import CampaignOrchestrator, GenerationConfig

try:
    config = GenerationConfig(openai_api_key="invalid-key")
    orchestrator = CampaignOrchestrator(config)
    campaign = orchestrator.generate_complete_campaign(brief)
    
except ValueError as e:
    print(f"Configuration error: {e}")
    
except Exception as e:
    if "rate limit" in str(e).lower():
        print("OpenAI rate limit exceeded. Please wait and try again.")
    elif "api key" in str(e).lower():
        print("Invalid OpenAI API key. Please check your configuration.")
    elif "insufficient credits" in str(e).lower():
        print("Insufficient OpenAI credits. Please add credits to your account.")
    else:
        print(f"Unexpected error: {e}")
```

### Validation

```python
from pydantic import ValidationError

try:
    brief = CampaignBrief(
        product_info=ProductInfo(
            name="",  # Invalid: empty name
            category="tech",
            description="A product",
            key_features=[],
            price_point="invalid",  # Invalid price point
            unique_selling_propositions=[]
        ),
        demographics=Demographics(
            age_range=(150, 200),  # Invalid age range
            income_level="medium",
            geographic_location=[],
            education_level="college"
        ),
        objectives=[],  # Invalid: empty objectives
        platforms=[]   # Invalid: empty platforms
    )
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Retry Logic

```python
import time
from typing import Optional

def generate_campaign_with_retry(
    orchestrator: CampaignOrchestrator, 
    brief: CampaignBrief, 
    max_retries: int = 3
) -> Optional[CampaignOutput]:
    """Generate campaign with retry logic for rate limits"""
    
    for attempt in range(max_retries):
        try:
            return orchestrator.generate_complete_campaign(brief)
        except Exception as e:
            if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limit hit. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                raise e
    
    return None
```

## Performance Considerations

### Cost Optimization

```python
# Use cheaper models for development
config = GenerationConfig(
    openai_api_key="your-key",
    model_text="gpt-3.5-turbo",  # Cheaper than gpt-4
    model_image="dall-e-2",      # Cheaper than gpt-image-1
    enable_image_generation=False,  # Disable for testing
    max_headlines=3,             # Reduce content volume
    max_taglines=2,
    max_ad_copy_variants=2
)
```

### Async Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def generate_campaign_async(brief: CampaignBrief) -> CampaignOutput:
    """Generate campaign asynchronously"""
    loop = asyncio.get_event_loop()
    
    with ThreadPoolExecutor() as executor:
        config = GenerationConfig(openai_api_key="your-key")
        orchestrator = CampaignOrchestrator(config)
        
        campaign = await loop.run_in_executor(
            executor, 
            orchestrator.generate_complete_campaign, 
            brief
        )
        
    return campaign

# Usage
campaign = await generate_campaign_async(brief)
```

---

**For more examples and advanced usage, see the [examples/](examples/) directory and [README.md](README.md).**

