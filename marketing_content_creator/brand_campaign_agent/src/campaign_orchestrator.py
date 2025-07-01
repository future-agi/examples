"""
Main campaign orchestrator that coordinates all generation components
"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from .models import (
    CampaignBrief, CampaignOutput, TextContent, BrandElements, 
    VisualAsset, GenerationConfig, ColorPalette, TypographyGuide
)
from .openai_client import CampaignGenerator
from .image_generator import ImageGenerator


class CampaignOrchestrator:
    """Main orchestrator for complete campaign generation"""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.campaign_generator = CampaignGenerator(config)
        self.image_generator = ImageGenerator(config)
        
        # Ensure output directory exists
        os.makedirs(config.output_directory, exist_ok=True)
    
    def generate_complete_campaign(self, brief: CampaignBrief) -> CampaignOutput:
        """Generate a complete brand campaign"""
        campaign_id = str(uuid.uuid4())[:8]
        print(f"Starting campaign generation (ID: {campaign_id})")
        
        # Create campaign-specific output directory
        campaign_dir = os.path.join(self.config.output_directory, f"campaign_{campaign_id}")
        os.makedirs(campaign_dir, exist_ok=True)
        
        # Update config to use campaign-specific directory
        self.config.output_directory = campaign_dir
        self.image_generator.output_dir = campaign_dir
        
        try:
            # Step 1: Generate brand elements first (needed for visual consistency)
            print("🎨 Generating brand elements...")
            brand_elements = self._generate_brand_elements(brief)
            
            # Step 2: Generate text content
            print("📝 Generating text content...")
            text_content = self.campaign_generator.generate_complete_campaign(brief)
            
            # Step 3: Generate visual assets
            print("🖼️ Generating visual assets...")
            visual_assets = self._generate_visual_assets(brief, brand_elements.color_palette)
            
            # Step 4: Create campaign summary
            print("📋 Creating campaign summary...")
            campaign_summary = self._generate_campaign_summary(brief, text_content, brand_elements)
            
            # Step 5: Generate recommendations
            print("💡 Generating recommendations...")
            recommendations = self._generate_recommendations(brief, text_content, visual_assets)
            
            # Create complete campaign output
            campaign_output = CampaignOutput(
                campaign_id=campaign_id,
                brief=brief,
                text_content=text_content,
                visual_assets=visual_assets,
                brand_elements=brand_elements,
                campaign_summary=campaign_summary,
                recommendations=recommendations,
                created_at=datetime.now().isoformat()
            )
            
            # Save campaign data
            self._save_campaign_output(campaign_output, campaign_dir)
            
            print(f"✅ Campaign generation complete! Output saved to: {campaign_dir}")
            return campaign_output
            
        except Exception as e:
            print(f"❌ Campaign generation failed: {str(e)}")
            raise
    
    def _generate_brand_elements(self, brief: CampaignBrief) -> BrandElements:
        """Generate complete brand elements"""
        # Generate color palette
        color_palette = self.campaign_generator.generate_color_palette(brief)
        
        # Generate typography guide
        typography = self.campaign_generator.generate_typography_guide(brief)
        
        # Generate logo concepts
        logo_concepts = self.image_generator.create_logo_concepts(brief, color_palette)
        
        # Generate brand personality description
        brand_personality = self._generate_brand_personality(brief)
        
        # Generate visual style description
        visual_style = self._generate_visual_style(brief, color_palette)
        
        return BrandElements(
            color_palette=color_palette,
            typography=typography,
            logo_concepts=logo_concepts,
            visual_style=visual_style,
            brand_personality=brand_personality
        )
    
    def _generate_visual_assets(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[VisualAsset]:
        """Generate all visual assets"""
        all_assets = []
        
        # Generate hero images
        hero_images = self.image_generator.generate_hero_images(brief, color_palette)
        all_assets.extend(hero_images)
        
        # Generate social media assets
        social_assets = self.image_generator.generate_social_media_assets(brief, color_palette)
        all_assets.extend(social_assets)
        
        # Generate product mockups
        mockups = self.image_generator.generate_product_mockups(brief, color_palette)
        all_assets.extend(mockups)
        
        # Generate supporting graphics
        graphics = self.image_generator.generate_supporting_graphics(brief, color_palette)
        all_assets.extend(graphics)
        
        return all_assets
    
    def _generate_brand_personality(self, brief: CampaignBrief) -> str:
        """Generate brand personality description"""
        prompt = f"""
        Define the brand personality for {brief.product_info.name}.
        
        Product: {brief.product_info.category}
        Target Audience: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years old
        Values: {', '.join(brief.demographics.values)}
        Price Point: {brief.product_info.price_point}
        Key Features: {', '.join(brief.product_info.key_features[:3])}
        
        Describe the brand personality in 2-3 sentences, covering:
        - Core personality traits
        - How the brand should feel to customers
        - The emotional connection it creates
        
        Write in a clear, professional tone.
        """
        
        return self.campaign_generator.openai_client.generate_text(prompt)
    
    def _generate_visual_style(self, brief: CampaignBrief, color_palette: ColorPalette) -> str:
        """Generate visual style description"""
        prompt = f"""
        Define the visual style guidelines for {brief.product_info.name} brand.
        
        Brand Context:
        - Category: {brief.product_info.category}
        - Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
        - Positioning: {brief.product_info.price_point}
        - Primary Color: {color_palette.primary}
        - Secondary Color: {color_palette.secondary}
        
        Describe the visual style in 2-3 sentences, covering:
        - Overall aesthetic approach
        - Visual elements and design principles
        - How visuals should support brand personality
        
        Be specific about style direction (modern, classic, minimalist, bold, etc.).
        """
        
        return self.campaign_generator.openai_client.generate_text(prompt)
    
    def _generate_campaign_summary(self, brief: CampaignBrief, text_content: TextContent, brand_elements: BrandElements) -> str:
        """Generate executive campaign summary"""
        prompt = f"""
        Create an executive summary for the {brief.product_info.name} brand campaign.
        
        Campaign Overview:
        - Product: {brief.product_info.name} ({brief.product_info.category})
        - Target: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years old
        - Objectives: {', '.join([obj.value for obj in brief.objectives])}
        - Platforms: {', '.join([p.value for p in brief.platforms])}
        
        Generated Content:
        - {len(text_content.headlines)} headlines
        - {len(text_content.taglines)} taglines
        - Ad copy for {len(text_content.ad_copy)} platforms
        - {len(text_content.product_descriptions)} product descriptions
        - Brand color palette and typography guide
        
        Write a comprehensive 3-4 paragraph executive summary covering:
        1. Campaign objectives and target audience
        2. Key messaging and creative approach
        3. Brand elements and visual direction
        4. Expected impact and next steps
        
        Use professional, strategic language appropriate for stakeholders.
        """
        
        return self.campaign_generator.openai_client.generate_text(prompt)
    
    def _generate_recommendations(self, brief: CampaignBrief, text_content: TextContent, visual_assets: List[VisualAsset]) -> List[str]:
        """Generate implementation recommendations"""
        prompt = f"""
        Provide 5-7 strategic recommendations for implementing the {brief.product_info.name} campaign.
        
        Campaign Context:
        - Target: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years old
        - Platforms: {', '.join([p.value for p in brief.platforms])}
        - Objectives: {', '.join([obj.value for obj in brief.objectives])}
        - Generated Assets: {len(visual_assets)} visual assets, multiple text variants
        
        Provide actionable recommendations for:
        - Content testing and optimization
        - Platform-specific deployment strategies
        - Performance measurement
        - Budget allocation
        - Timeline considerations
        - Brand consistency maintenance
        
        Each recommendation should be specific, actionable, and strategic.
        Return one recommendation per line.
        """
        
        response = self.campaign_generator.openai_client.generate_text(prompt)
        recommendations = [line.strip() for line in response.split('\n') if line.strip()]
        return recommendations
    
    def _save_campaign_output(self, campaign_output: CampaignOutput, output_dir: str):
        """Save campaign output in multiple formats"""
        # Save as JSON
        json_path = os.path.join(output_dir, "campaign_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(campaign_output.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Save text content as separate files
        text_dir = os.path.join(output_dir, "text_content")
        os.makedirs(text_dir, exist_ok=True)
        
        # Headlines
        with open(os.path.join(text_dir, "headlines.txt"), 'w', encoding='utf-8') as f:
            f.write('\n'.join(campaign_output.text_content.headlines))
        
        # Taglines
        with open(os.path.join(text_dir, "taglines.txt"), 'w', encoding='utf-8') as f:
            f.write('\n'.join(campaign_output.text_content.taglines))
        
        # Ad copy by platform
        for platform, copy_list in campaign_output.text_content.ad_copy.items():
            with open(os.path.join(text_dir, f"ad_copy_{platform}.txt"), 'w', encoding='utf-8') as f:
                f.write('\n\n---\n\n'.join(copy_list))
        
        # Product descriptions
        with open(os.path.join(text_dir, "product_descriptions.txt"), 'w', encoding='utf-8') as f:
            f.write('\n\n---\n\n'.join(campaign_output.text_content.product_descriptions))
        
        # Call-to-actions
        with open(os.path.join(text_dir, "call_to_actions.txt"), 'w', encoding='utf-8') as f:
            f.write('\n'.join(campaign_output.text_content.call_to_actions))
        
        # Social media posts
        for platform, posts in campaign_output.text_content.social_media_posts.items():
            with open(os.path.join(text_dir, f"social_posts_{platform}.txt"), 'w', encoding='utf-8') as f:
                f.write('\n\n---\n\n'.join(posts))
        
        # Save brand elements
        brand_dir = os.path.join(output_dir, "brand_elements")
        os.makedirs(brand_dir, exist_ok=True)
        
        # Color palette
        with open(os.path.join(brand_dir, "color_palette.json"), 'w', encoding='utf-8') as f:
            json.dump(campaign_output.brand_elements.color_palette.model_dump(), f, indent=2)
        
        # Typography guide
        with open(os.path.join(brand_dir, "typography_guide.txt"), 'w', encoding='utf-8') as f:
            typo = campaign_output.brand_elements.typography
            f.write(f"Primary Font: {typo.primary_font}\n")
            f.write(f"Secondary Font: {typo.secondary_font}\n")
            f.write(f"Heading Style: {typo.heading_style}\n")
            f.write(f"Body Style: {typo.body_style}\n")
            f.write(f"Rationale: {typo.font_pairing_rationale}\n")
        
        # Logo concepts
        with open(os.path.join(brand_dir, "logo_concepts.txt"), 'w', encoding='utf-8') as f:
            for i, concept in enumerate(campaign_output.brand_elements.logo_concepts, 1):
                f.write(f"Concept {i}:\n{concept}\n\n---\n\n")
        
        # Brand guidelines
        with open(os.path.join(brand_dir, "brand_guidelines.md"), 'w', encoding='utf-8') as f:
            f.write(f"# {campaign_output.brief.product_info.name} Brand Guidelines\n\n")
            f.write(f"## Brand Personality\n{campaign_output.brand_elements.brand_personality}\n\n")
            f.write(f"## Visual Style\n{campaign_output.brand_elements.visual_style}\n\n")
            f.write(f"## Color Palette\n")
            palette = campaign_output.brand_elements.color_palette
            f.write(f"- Primary: {palette.primary}\n")
            f.write(f"- Secondary: {palette.secondary}\n")
            f.write(f"- Accent: {palette.accent}\n")
            f.write(f"- Neutral: {palette.neutral}\n")
            f.write(f"- Background: {palette.background}\n")
            f.write(f"- Text: {palette.text}\n\n")
            f.write(f"### Color Psychology\n{palette.psychology}\n\n")
        
        # Save campaign summary and recommendations
        with open(os.path.join(output_dir, "campaign_summary.md"), 'w', encoding='utf-8') as f:
            f.write(f"# {campaign_output.brief.product_info.name} Campaign Summary\n\n")
            f.write(f"{campaign_output.campaign_summary}\n\n")
            f.write(f"## Implementation Recommendations\n\n")
            for i, rec in enumerate(campaign_output.recommendations, 1):
                f.write(f"{i}. {rec}\n")
        
        print(f"📁 Campaign files saved to: {output_dir}")
        print(f"   - JSON data: campaign_data.json")
        print(f"   - Text content: text_content/")
        print(f"   - Brand elements: brand_elements/")
        print(f"   - Visual assets: visual_assets/")
        print(f"   - Summary: campaign_summary.md")

