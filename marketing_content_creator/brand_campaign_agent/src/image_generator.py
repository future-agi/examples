"""
Image generation engine for brand campaigns using DALL-E
"""
import os
import json
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import requests
import io
from .models import (
    CampaignBrief, VisualAsset, ColorPalette, PlatformType, GenerationConfig
)
from .openai_client import OpenAIClient


class ImageGenerator:
    """Handles all image generation and visual asset creation"""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.openai_client = OpenAIClient(config)
        self.output_dir = config.output_directory
        
    def generate_hero_images(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]:
        """Generate main campaign hero images"""
        if not self.config.enable_image_generation:
            return []
            
        hero_images = []
        
        # Generate 3 different hero image concepts
        concepts = [
            "lifestyle and aspirational",
            "product-focused and clean",
            "emotional and storytelling"
        ]
        
        for i, concept in enumerate(concepts):
            prompt = self._create_hero_image_prompt(brief, color_palette, concept)
            filename = f"visual_assets/hero_images/hero_image_{i+1}_{concept.replace(' ', '_')}.png"
            
            try:
                filepath = self.openai_client.generate_image(prompt, filename)
                if filepath:
                    hero_images.append(VisualAsset(
                        filename=filename,
                        asset_type="hero_image",
                        description=f"Hero image with {concept} approach",
                        dimensions=(1024, 1024),
                        platform_optimized=[PlatformType.WEBSITE, PlatformType.FACEBOOK]
                    ))
            except Exception as e:
                print(f"Failed to generate hero image {i+1}: {e}")
                
        return hero_images
    
    def generate_social_media_assets(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]:
        """Generate platform-specific social media images"""
        if not self.config.enable_image_generation:
            return []
            
        social_assets = []
        
        # Platform-specific image requirements
        platform_specs = {
            PlatformType.INSTAGRAM: {
                "sizes": [(1080, 1080), (1080, 1350)],
                "style": "trendy and aesthetic",
                "names": ["instagram_square", "instagram_portrait"]
            },
            PlatformType.FACEBOOK: {
                "sizes": [(1200, 630)],
                "style": "engaging and community-focused",
                "names": ["facebook_post"]
            },
            PlatformType.TWITTER: {
                "sizes": [(1200, 675)],
                "style": "bold and attention-grabbing",
                "names": ["twitter_post"]
            },
            PlatformType.LINKEDIN: {
                "sizes": [(1200, 627)],
                "style": "professional and trustworthy",
                "names": ["linkedin_post"]
            }
        }
        
        for platform in brief.platforms:
            if platform in platform_specs:
                spec = platform_specs[platform]
                for i, (width, height) in enumerate(spec["sizes"]):
                    prompt = self._create_social_media_prompt(brief, color_palette, spec["style"], width, height)
                    filename = f"visual_assets/social_media/{spec['names'][i]}.png"
                    
                    try:
                        filepath = self.openai_client.generate_image(prompt, filename)
                        if filepath:
                            social_assets.append(VisualAsset(
                                filename=filename,
                                asset_type="social_media",
                                description=f"{platform.value} optimized image",
                                dimensions=(width, height),
                                platform_optimized=[platform]
                            ))
                    except Exception as e:
                        print(f"Failed to generate {platform.value} image: {e}")
        
        return social_assets
    
    def generate_product_mockups(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]:
        """Generate product mockup images"""
        if not self.config.enable_image_generation:
            return []
            
        mockups = []
        
        # Different mockup contexts
        contexts = [
            "in use by target demographic",
            "in lifestyle setting",
            "product showcase with clean background"
        ]
        
        for i, context in enumerate(contexts):
            prompt = self._create_product_mockup_prompt(brief, color_palette, context)
            filename = f"visual_assets/product_mockups/mockup_{i+1}_{context.replace(' ', '_')}.png"
            
            try:
                filepath = self.openai_client.generate_image(prompt, filename)
                if filepath:
                    mockups.append(VisualAsset(
                        filename=filename,
                        asset_type="product_mockup",
                        description=f"Product mockup {context}",
                        dimensions=(1024, 1024),
                        platform_optimized=[PlatformType.WEBSITE, PlatformType.EMAIL]
                    ))
            except Exception as e:
                print(f"Failed to generate product mockup {i+1}: {e}")
                
        return mockups
    
    def generate_supporting_graphics(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]:
        """Generate supporting visual elements"""
        if not self.config.enable_image_generation:
            return []
            
        graphics = []
        
        # Generate background patterns
        pattern_prompt = f"""
        Create an abstract background pattern for {brief.product_info.name} brand.
        Use colors: {color_palette.primary}, {color_palette.secondary}, {color_palette.accent}.
        Style: modern, subtle, professional.
        The pattern should be seamless and work as a background element.
        No text or logos, just geometric or organic patterns.
        """
        
        try:
            filepath = self.openai_client.generate_image(pattern_prompt, "visual_assets/supporting_graphics/background_pattern.png")
            if filepath:
                graphics.append(VisualAsset(
                    filename="visual_assets/supporting_graphics/background_pattern.png",
                    asset_type="background_pattern",
                    description="Brand background pattern",
                    dimensions=(1024, 1024),
                    platform_optimized=[PlatformType.WEBSITE, PlatformType.EMAIL]
                ))
        except Exception as e:
            print(f"Failed to generate background pattern: {e}")
        
        # Generate icon-style graphics
        icon_prompt = f"""
        Create a set of simple, modern icons representing {brief.product_info.category} concepts.
        Style: minimalist, clean lines, single color ({color_palette.primary}).
        Include icons for: {', '.join(brief.product_info.key_features[:3])}.
        Arrange 3-4 icons in a grid layout.
        """
        
        try:
            filepath = self.openai_client.generate_image(icon_prompt, "visual_assets/supporting_graphics/icon_set.png")
            if filepath:
                graphics.append(VisualAsset(
                    filename="visual_assets/supporting_graphics/icon_set.png",
                    asset_type="icon_set",
                    description="Brand icon set",
                    dimensions=(1024, 1024),
                    platform_optimized=[PlatformType.WEBSITE, PlatformType.PRINT]
                ))
        except Exception as e:
            print(f"Failed to generate icon set: {e}")
            
        return graphics
    
    def create_logo_concepts(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[str]:
        """Generate logo concept descriptions (not actual logos)"""
        prompt = f"""
        Create 3 detailed logo concept descriptions for {brief.product_info.name}.
        
        Brand Information:
        - Category: {brief.product_info.category}
        - Positioning: {brief.product_info.price_point}
        - Key Values: {', '.join(brief.demographics.values[:3])}
        - Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
        
        Color Palette:
        - Primary: {color_palette.primary}
        - Secondary: {color_palette.secondary}
        - Accent: {color_palette.accent}
        
        For each concept, describe:
        - Visual style and approach
        - Typography treatment
        - Color usage
        - Symbolic elements
        - Overall personality conveyed
        
        Make each concept distinct and appropriate for the target audience.
        Separate concepts with "---"
        """
        
        response = self.openai_client.generate_text(prompt)
        concepts = [concept.strip() for concept in response.split('---') if concept.strip()]
        return concepts[:3]
    
    def generate_brand_style_guide_visual(self, color_palette: ColorPalette, typography_guide: Any) -> str:
        """Create a visual brand style guide"""
        try:
            # Create a simple brand guide image using PIL
            width, height = 1200, 1600
            img = Image.new('RGB', (width, height), color=color_palette.background)
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
                header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
            
            y_pos = 50
            
            # Title
            draw.text((50, y_pos), "Brand Style Guide", fill=color_palette.text, font=title_font)
            y_pos += 100
            
            # Color palette section
            draw.text((50, y_pos), "Color Palette", fill=color_palette.text, font=header_font)
            y_pos += 50
            
            colors = [
                ("Primary", color_palette.primary),
                ("Secondary", color_palette.secondary),
                ("Accent", color_palette.accent),
                ("Neutral", color_palette.neutral)
            ]
            
            for i, (name, color) in enumerate(colors):
                x_pos = 50 + (i * 250)
                # Draw color swatch
                draw.rectangle([x_pos, y_pos, x_pos + 100, y_pos + 100], fill=color)
                # Draw color name and hex
                draw.text((x_pos, y_pos + 110), name, fill=color_palette.text, font=body_font)
                draw.text((x_pos, y_pos + 135), color, fill=color_palette.text, font=body_font)
            
            y_pos += 200
            
            # Typography section
            draw.text((50, y_pos), "Typography", fill=color_palette.text, font=header_font)
            y_pos += 50
            draw.text((50, y_pos), f"Primary Font: {typography_guide.primary_font}", fill=color_palette.text, font=body_font)
            y_pos += 30
            draw.text((50, y_pos), f"Secondary Font: {typography_guide.secondary_font}", fill=color_palette.text, font=body_font)
            
            # Save the image
            filepath = os.path.join(self.output_dir, "brand_elements/style_guide_visual.png")
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            img.save(filepath)
            
            return filepath
            
        except Exception as e:
            print(f"Failed to create style guide visual: {e}")
            return ""
    
    def _create_hero_image_prompt(self, brief: CampaignBrief, color_palette: ColorPalette, concept: str) -> str:
        """Create prompt for hero image generation"""
        return f"""
        Create a high-quality hero image for {brief.product_info.name} campaign with {concept} approach.
        
        Product: {brief.product_info.category} - {brief.product_info.name}
        Target Audience: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years old
        Brand Colors: {color_palette.primary}, {color_palette.secondary}, {color_palette.accent}
        
        Key Elements to Include:
        - {', '.join(brief.product_info.key_features[:2])}
        - Appeal to {', '.join(brief.demographics.values[:2])}
        
        Style Requirements:
        - Professional and modern
        - High-quality, commercial photography style
        - Incorporate brand colors naturally
        - {concept} aesthetic
        - No text or logos in the image
        - Suitable for web and print use
        """
    
    def _create_social_media_prompt(self, brief: CampaignBrief, color_palette: ColorPalette, style: str, width: int, height: int) -> str:
        """Create prompt for social media image generation"""
        return f"""
        Create a {style} social media image for {brief.product_info.name}.
        
        Dimensions: {width}x{height} pixels
        Product Category: {brief.product_info.category}
        Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
        Brand Colors: {color_palette.primary}, {color_palette.secondary}
        
        Style: {style}
        Key Message: {brief.product_info.unique_selling_propositions[0] if brief.product_info.unique_selling_propositions else 'Quality and innovation'}
        
        Requirements:
        - Eye-catching and scroll-stopping
        - Leave space for text overlay
        - Brand color integration
        - Target audience appeal
        - No text in the image itself
        """
    
    def _create_product_mockup_prompt(self, brief: CampaignBrief, color_palette: ColorPalette, context: str) -> str:
        """Create prompt for product mockup generation"""
        return f"""
        Create a product mockup showing {brief.product_info.name} {context}.
        
        Product: {brief.product_info.category}
        Context: {context}
        Target Demographic: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years old
        Brand Colors: {color_palette.primary}, {color_palette.secondary}
        
        Requirements:
        - Realistic and professional
        - Show product clearly
        - Appropriate setting for target audience
        - Good lighting and composition
        - Brand colors in environment/styling
        - Commercial photography quality
        """

