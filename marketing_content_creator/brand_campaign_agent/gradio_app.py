#!/usr/bin/env python3
"""
Standalone Gradio Application for OpenAI Brand Campaign Agent

This file provides a complete Gradio web interface for the Brand Campaign Agent.
Run this file directly to launch the web interface.

Usage:
    python gradio_app.py

Requirements:
    - OpenAI API key set in environment variable OPENAI_API_KEY
    - All dependencies installed (see requirements.txt)
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import gradio as gr
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from models import *
    from openai_client import OpenAIClient
    from campaign_orchestrator import CampaignOrchestrator
    print("✅ Imported from existing modules")
except ImportError:
    # If modules don't exist, define them inline
    print("📦 Using inline implementations")
    
    import openai
    from pydantic import BaseModel, Field
    from enum import Enum
    
    # Inline model definitions (same as in notebook)
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
        age_range: Tuple[int, int] = Field(description="Age range (min, max)")
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
        name: str = Field(description="Product/service name")
        category: str = Field(description="Product category")
        description: str = Field(description="Detailed product description")
        key_features: List[str] = Field(description="Main features and benefits")
        price_point: str = Field(description="Price positioning (budget, mid-range, premium, luxury)")
        unique_selling_propositions: List[str] = Field(description="What makes it unique")
        competitors: List[str] = Field(description="Main competitors", default=[])

    class CampaignBrief(BaseModel):
        product_info: ProductInfo
        demographics: Demographics
        objectives: List[CampaignObjective]
        platforms: List[PlatformType]
        budget_range: Optional[str] = None
        timeline: Optional[str] = None
        additional_context: Optional[str] = None

    class ColorPalette(BaseModel):
        primary: str = Field(description="Primary brand color (hex)")
        secondary: str = Field(description="Secondary brand color (hex)")
        accent: str = Field(description="Accent color (hex)")
        neutral: str = Field(description="Neutral color (hex)")
        background: str = Field(description="Background color (hex)")
        text: str = Field(description="Text color (hex)")
        psychology: str = Field(description="Color psychology explanation")

    class TypographyGuide(BaseModel):
        primary_font: str = Field(description="Primary font family")
        secondary_font: str = Field(description="Secondary font family")
        heading_style: str = Field(description="Heading typography style")
        body_style: str = Field(description="Body text typography style")
        font_pairing_rationale: str = Field(description="Why these fonts work together")

    class TextContent(BaseModel):
        headlines: List[str] = Field(description="Campaign headlines")
        taglines: List[str] = Field(description="Brand taglines")
        ad_copy: Dict[str, List[str]] = Field(description="Ad copy by platform")
        product_descriptions: List[str] = Field(description="Product descriptions")
        call_to_actions: List[str] = Field(description="Call-to-action phrases")
        social_media_posts: Dict[str, List[str]] = Field(description="Social media content by platform")

    class BrandElements(BaseModel):
        color_palette: ColorPalette
        typography: TypographyGuide
        logo_concepts: List[str] = Field(description="Logo concept descriptions")
        visual_style: str = Field(description="Overall visual style description")
        brand_personality: str = Field(description="Brand personality description")

    class CampaignOutput(BaseModel):
        campaign_id: str = Field(description="Unique campaign identifier")
        brief: CampaignBrief = Field(description="Original campaign brief")
        text_content: TextContent = Field(description="Generated text content")
        brand_elements: BrandElements = Field(description="Brand design elements")
        campaign_summary: str = Field(description="Executive summary of the campaign")
        recommendations: List[str] = Field(description="Implementation recommendations")
        created_at: str = Field(description="Creation timestamp")

    # Inline OpenAI client
    class OpenAIClient:
        def __init__(self, api_key: str):
            self.client = openai.OpenAI(api_key=api_key)
        
        def generate_text(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                content = response.choices[0].message.content
                return content.strip() if content else ""
            except Exception as e:
                raise Exception(f"Text generation failed: {str(e)}")

    # Inline campaign generator (simplified)
    class CampaignGenerator:
        def __init__(self, api_key: str):
            self.openai_client = OpenAIClient(api_key)
        
        def generate_headlines(self, brief: CampaignBrief, max_headlines: int = 5) -> List[str]:
            prompt = f"""
            Create {max_headlines} compelling headlines for a {brief.product_info.category} campaign.
            
            Product: {brief.product_info.name}
            Description: {brief.product_info.description}
            Key Features: {', '.join(brief.product_info.key_features)}
            USPs: {', '.join(brief.product_info.unique_selling_propositions)}
            
            Target Audience:
            - Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
            - Income: {brief.demographics.income_level}
            - Interests: {', '.join(brief.demographics.interests)}
            - Values: {', '.join(brief.demographics.values)}
            
            Campaign Objectives: {', '.join([obj.value for obj in brief.objectives])}
            
            Requirements:
            - Headlines should be catchy, memorable, and under 60 characters
            - Appeal to the target demographic's values and interests
            - Highlight key benefits and unique selling propositions
            - Match the campaign objectives
            
            Return only the headlines, one per line, without numbering or bullets.
            """
            
            response = self.openai_client.generate_text(prompt)
            headlines = [line.strip() for line in response.split('\n') if line.strip()]
            return headlines[:max_headlines]
        
        def generate_taglines(self, brief: CampaignBrief, max_taglines: int = 3) -> List[str]:
            prompt = f"""
            Create {max_taglines} memorable taglines for {brief.product_info.name}.
            
            Product Category: {brief.product_info.category}
            Brand Positioning: {brief.product_info.price_point}
            Key Values: {', '.join(brief.demographics.values)}
            
            Requirements:
            - Taglines should be short (under 30 characters)
            - Memorable and brandable
            - Reflect the product's unique value
            - Resonate with target audience values
            
            Return only the taglines, one per line.
            """
            
            response = self.openai_client.generate_text(prompt)
            taglines = [line.strip() for line in response.split('\n') if line.strip()]
            return taglines[:max_taglines]
        
        def generate_ad_copy(self, brief: CampaignBrief, max_variants: int = 3) -> Dict[str, List[str]]:
            ad_copy = {}
            
            platform_requirements = {
                "facebook": "Conversational tone, 125 characters or less, focus on community",
                "instagram": "Visual-first approach, lifestyle-focused, use relevant hashtags",
                "twitter": "Concise and punchy, 280 characters max, trending awareness",
                "linkedin": "Professional tone, business value focus, industry expertise",
                "google_ads": "Clear value proposition, strong CTA, keyword optimization",
                "email": "Personal tone, subject line optimization, clear hierarchy",
                "website": "SEO-friendly, conversion-focused, user experience priority",
                "print": "Traditional advertising, clear hierarchy, brand prominence"
            }
            
            for platform in brief.platforms:
                platform_key = platform.value
                requirements = platform_requirements.get(platform_key, "Standard advertising copy")
                
                prompt = f"""
                Create {max_variants} ad copy variants for {platform_key}.
                
                Product: {brief.product_info.name}
                Category: {brief.product_info.category}
                Key Features: {', '.join(brief.product_info.key_features)}
                Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
                
                Platform requirements: {requirements}
                
                Each variant should:
                - Hook the reader immediately
                - Highlight key benefits
                - Include a strong call-to-action
                - Match the platform's tone and format
                
                Return each variant separated by "---"
                """
                
                response = self.openai_client.generate_text(prompt)
                variants = [variant.strip() for variant in response.split('---') if variant.strip()]
                ad_copy[platform_key] = variants[:max_variants]
            
            return ad_copy
        
        def generate_color_palette(self, brief: CampaignBrief) -> ColorPalette:
            prompt = f"""
            Create a color palette for {brief.product_info.name} in the {brief.product_info.category} category.
            
            Brand Positioning: {brief.product_info.price_point}
            Target Demographics: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years old
            Target Values: {', '.join(brief.demographics.values)}
            Product Personality: {', '.join(brief.product_info.key_features[:3])}
            
            Return a JSON object with:
            - primary: main brand color (hex)
            - secondary: supporting color (hex)
            - accent: highlight color (hex)
            - neutral: neutral color (hex)
            - background: background color (hex)
            - text: text color (hex)
            - psychology: explanation of color choices and psychological impact
            
            Consider color psychology and ensure accessibility.
            """
            
            response = self.openai_client.generate_text(prompt)
            try:
                color_data = json.loads(response)
                return ColorPalette(**color_data)
            except:
                return ColorPalette(
                    primary="#2563eb",
                    secondary="#64748b",
                    accent="#f59e0b",
                    neutral="#6b7280",
                    background="#ffffff",
                    text="#1f2937",
                    psychology="Professional and trustworthy color scheme"
                )
        
        def generate_typography_guide(self, brief: CampaignBrief) -> TypographyGuide:
            prompt = f"""
            Recommend typography for {brief.product_info.name} brand.
            
            Brand Category: {brief.product_info.category}
            Price Point: {brief.product_info.price_point}
            Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
            Brand Values: {', '.join(brief.demographics.values[:3])}
            
            Return a JSON object with:
            - primary_font: main font family name
            - secondary_font: supporting font family name
            - heading_style: description of heading typography style
            - body_style: description of body text style
            - font_pairing_rationale: why these fonts work together
            
            Consider readability, brand personality, and target audience preferences.
            """
            
            response = self.openai_client.generate_text(prompt)
            try:
                typo_data = json.loads(response)
                return TypographyGuide(**typo_data)
            except:
                return TypographyGuide(
                    primary_font="Inter",
                    secondary_font="Merriweather",
                    heading_style="Bold, modern sans-serif for impact",
                    body_style="Clean, readable serif for trust",
                    font_pairing_rationale="Modern sans-serif paired with classic serif for balance"
                )

    # Simplified orchestrator
    class CampaignOrchestrator:
        def __init__(self, api_key: str):
            self.campaign_generator = CampaignGenerator(api_key)
            self.openai_client = OpenAIClient(api_key)
        
        def generate_complete_campaign(self, brief: CampaignBrief) -> CampaignOutput:
            campaign_id = str(uuid.uuid4())[:8]
            
            # Generate brand elements
            color_palette = self.campaign_generator.generate_color_palette(brief)
            typography = self.campaign_generator.generate_typography_guide(brief)
            
            # Generate text content
            headlines = self.campaign_generator.generate_headlines(brief)
            taglines = self.campaign_generator.generate_taglines(brief)
            ad_copy = self.campaign_generator.generate_ad_copy(brief)
            
            # Generate additional content
            product_descriptions = self._generate_product_descriptions(brief)
            call_to_actions = self._generate_call_to_actions(brief)
            social_media_posts = self._generate_social_media_posts(brief)
            
            # Generate brand personality and visual style
            brand_personality = self._generate_brand_personality(brief)
            visual_style = self._generate_visual_style(brief, color_palette)
            logo_concepts = self._generate_logo_concepts(brief, color_palette)
            
            brand_elements = BrandElements(
                color_palette=color_palette,
                typography=typography,
                logo_concepts=logo_concepts,
                visual_style=visual_style,
                brand_personality=brand_personality
            )
            
            text_content = TextContent(
                headlines=headlines,
                taglines=taglines,
                ad_copy=ad_copy,
                product_descriptions=product_descriptions,
                call_to_actions=call_to_actions,
                social_media_posts=social_media_posts
            )
            
            # Generate campaign summary and recommendations
            campaign_summary = self._generate_campaign_summary(brief, text_content, brand_elements)
            recommendations = self._generate_recommendations(brief)
            
            return CampaignOutput(
                campaign_id=campaign_id,
                brief=brief,
                text_content=text_content,
                brand_elements=brand_elements,
                campaign_summary=campaign_summary,
                recommendations=recommendations,
                created_at=datetime.now().isoformat()
            )
        
        def _generate_brand_personality(self, brief: CampaignBrief) -> str:
            prompt = f"""
            Define the brand personality for {brief.product_info.name}.
            
            Product: {brief.product_info.category}
            Target Audience: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years old
            Values: {', '.join(brief.demographics.values)}
            Price Point: {brief.product_info.price_point}
            
            Describe the brand personality in 2-3 sentences.
            """
            return self.openai_client.generate_text(prompt)
        
        def _generate_visual_style(self, brief: CampaignBrief, color_palette: ColorPalette) -> str:
            prompt = f"""
            Define the visual style for {brief.product_info.name} brand.
            
            Category: {brief.product_info.category}
            Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
            Primary Color: {color_palette.primary}
            
            Describe the visual style in 2-3 sentences.
            """
            return self.openai_client.generate_text(prompt)
        
        def _generate_logo_concepts(self, brief: CampaignBrief, color_palette: ColorPalette) -> List[str]:
            prompt = f"""
            Create 3 logo concept descriptions for {brief.product_info.name}.
            
            Brand: {brief.product_info.category}
            Colors: {color_palette.primary}, {color_palette.secondary}
            
            Describe each concept in detail. Separate with "---"
            """
            response = self.openai_client.generate_text(prompt)
            concepts = [concept.strip() for concept in response.split('---') if concept.strip()]
            return concepts[:3]
        
        def _generate_product_descriptions(self, brief: CampaignBrief) -> List[str]:
            prompt = f"""
            Create 3 product descriptions for {brief.product_info.name}:
            1. Short (50-75 words)
            2. Medium (100-150 words)
            3. Long (200-250 words)
            
            Product: {brief.product_info.description}
            Features: {', '.join(brief.product_info.key_features)}
            
            Separate each with "---"
            """
            response = self.openai_client.generate_text(prompt)
            descriptions = [desc.strip() for desc in response.split('---') if desc.strip()]
            return descriptions
        
        def _generate_call_to_actions(self, brief: CampaignBrief) -> List[str]:
            prompt = f"""
            Create 8 call-to-action phrases for {brief.product_info.name}.
            
            Objectives: {', '.join([obj.value for obj in brief.objectives])}
            Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
            
            Make them action-oriented and compelling. One per line.
            """
            response = self.openai_client.generate_text(prompt)
            ctas = [line.strip() for line in response.split('\n') if line.strip()]
            return ctas
        
        def _generate_social_media_posts(self, brief: CampaignBrief) -> Dict[str, List[str]]:
            social_platforms = [p for p in brief.platforms if p.value in ['facebook', 'instagram', 'twitter', 'linkedin']]
            social_content = {}
            
            for platform in social_platforms:
                prompt = f"""
                Create 3 social media posts for {platform.value} promoting {brief.product_info.name}.
                
                Product: {brief.product_info.name}
                Features: {', '.join(brief.product_info.key_features[:3])}
                
                Make them platform-appropriate. Separate with "---"
                """
                response = self.openai_client.generate_text(prompt)
                posts = [post.strip() for post in response.split('---') if post.strip()]
                social_content[platform.value] = posts
            
            return social_content
        
        def _generate_campaign_summary(self, brief: CampaignBrief, text_content: TextContent, brand_elements: BrandElements) -> str:
            prompt = f"""
            Create an executive summary for the {brief.product_info.name} campaign.
            
            Product: {brief.product_info.name}
            Target: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years
            Objectives: {', '.join([obj.value for obj in brief.objectives])}
            Platforms: {', '.join([p.value for p in brief.platforms])}
            
            Write a comprehensive 3-4 paragraph summary.
            """
            return self.openai_client.generate_text(prompt)
        
        def _generate_recommendations(self, brief: CampaignBrief) -> List[str]:
            prompt = f"""
            Provide 6 strategic recommendations for implementing the {brief.product_info.name} campaign.
            
            Target: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]} years
            Platforms: {', '.join([p.value for p in brief.platforms])}
            
            Focus on actionable, strategic advice. One per line.
            """
            response = self.openai_client.generate_text(prompt)
            recommendations = [line.strip() for line in response.split('\n') if line.strip()]
            return recommendations


def load_environment():
    """Load environment variables and check API key"""
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='sk-your-openai-api-key-here'")
        print("Or create a .env file with: OPENAI_API_KEY=sk-your-openai-api-key-here")
        return None
    
    print("✅ OpenAI API key loaded successfully!")
    return api_key


def create_gradio_interface(api_key: str):
    """Create the main Gradio interface"""
    
    def generate_campaign_gradio(
        # Product Info
        product_name, product_category, product_description, 
        key_features, price_point, usps,
        # Demographics
        age_min, age_max, income_level, education_level,
        locations, interests, values,
        # Campaign
        objectives, platforms,
        # Optional
        budget_range, timeline, additional_context
    ):
        """Generate campaign using Gradio inputs"""
        
        try:
            # Parse inputs
            key_features_list = [f.strip() for f in key_features.split(',') if f.strip()]
            usps_list = [u.strip() for u in usps.split(',') if u.strip()] if usps else []
            locations_list = [l.strip() for l in locations.split(',') if l.strip()]
            interests_list = [i.strip() for i in interests.split(',') if i.strip()] if interests else []
            values_list = [v.strip() for v in values.split(',') if v.strip()] if values else []
            objectives_list = [CampaignObjective(obj) for obj in objectives]
            platforms_list = [PlatformType(platform) for platform in platforms]
            
            # Create campaign brief
            brief = CampaignBrief(
                product_info=ProductInfo(
                    name=product_name,
                    category=product_category,
                    description=product_description,
                    key_features=key_features_list,
                    price_point=price_point,
                    unique_selling_propositions=usps_list
                ),
                demographics=Demographics(
                    age_range=(age_min, age_max),
                    income_level=income_level,
                    geographic_location=locations_list,
                    education_level=education_level,
                    interests=interests_list,
                    values=values_list
                ),
                objectives=objectives_list,
                platforms=platforms_list,
                budget_range=budget_range if budget_range else None,
                timeline=timeline if timeline else None,
                additional_context=additional_context if additional_context else None
            )
            
            # Generate campaign
            orchestrator = CampaignOrchestrator(api_key)
            campaign = orchestrator.generate_complete_campaign(brief)
            
            # Format outputs
            headlines_output = "\n".join([f"• {h}" for h in campaign.text_content.headlines])
            taglines_output = "\n".join([f"• {t}" for t in campaign.text_content.taglines])
            
            # Ad copy by platform
            ad_copy_output = ""
            for platform, copies in campaign.text_content.ad_copy.items():
                ad_copy_output += f"**{platform.upper()}:**\n"
                for i, copy in enumerate(copies, 1):
                    ad_copy_output += f"{i}. {copy}\n\n"
                ad_copy_output += "---\n\n"
            
            # Brand elements
            brand_output = f"""**Color Palette:**
• Primary: {campaign.brand_elements.color_palette.primary}
• Secondary: {campaign.brand_elements.color_palette.secondary}
• Accent: {campaign.brand_elements.color_palette.accent}
• Neutral: {campaign.brand_elements.color_palette.neutral}
• Background: {campaign.brand_elements.color_palette.background}
• Text: {campaign.brand_elements.color_palette.text}

**Color Psychology:**
{campaign.brand_elements.color_palette.psychology}

**Typography:**
• Primary Font: {campaign.brand_elements.typography.primary_font}
• Secondary Font: {campaign.brand_elements.typography.secondary_font}
• Heading Style: {campaign.brand_elements.typography.heading_style}
• Body Style: {campaign.brand_elements.typography.body_style}
• Rationale: {campaign.brand_elements.typography.font_pairing_rationale}

**Brand Personality:**
{campaign.brand_elements.brand_personality}

**Visual Style:**
{campaign.brand_elements.visual_style}
"""
            
            # Product descriptions
            descriptions_output = "\n\n---\n\n".join(campaign.text_content.product_descriptions)
            
            # Campaign summary and recommendations
            summary_output = f"""**Campaign Summary:**
{campaign.campaign_summary}

**Implementation Recommendations:**
"""
            for i, rec in enumerate(campaign.recommendations, 1):
                summary_output += f"{i}. {rec}\n"
            
            return (
                f"✅ Campaign '{campaign.campaign_id}' generated successfully!",
                headlines_output,
                taglines_output,
                ad_copy_output,
                brand_output,
                descriptions_output,
                summary_output
            )
            
        except Exception as e:
            error_msg = f"❌ Campaign generation failed: {str(e)}"
            return error_msg, "", "", "", "", "", ""
    
    # Create the Gradio interface
    with gr.Blocks(
        title="🚀 OpenAI Brand Campaign Agent",
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .tab-nav {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        """
    ) as interface:
        
        gr.Markdown(
            """
            # 🚀 OpenAI Brand Campaign Agent
            
            Generate comprehensive brand campaigns with AI-powered content, visuals, and brand elements.
            
            **Features:** Headlines, Taglines, Ad Copy, Brand Colors, Typography, Product Descriptions, and Strategic Recommendations
            """
        )
        
        with gr.Tabs():
            with gr.Tab("📝 Campaign Brief"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🏷️ Product Information")
                        product_name = gr.Textbox(
                            label="Product Name",
                            placeholder="e.g., EcoSmart Water Bottle",
                            value="EcoSmart Water Bottle"
                        )
                        product_category = gr.Textbox(
                            label="Product Category",
                            placeholder="e.g., sustainable lifestyle product",
                            value="sustainable lifestyle product"
                        )
                        product_description = gr.Textbox(
                            label="Product Description",
                            placeholder="Describe your product or service...",
                            lines=3,
                            value="A smart water bottle that tracks hydration and is made from recycled materials"
                        )
                        key_features = gr.Textbox(
                            label="Key Features (comma-separated)",
                            placeholder="Smart tracking, Eco-friendly, Temperature control",
                            value="Smart hydration tracking, Made from 100% recycled materials, Temperature control technology, Mobile app integration"
                        )
                        price_point = gr.Dropdown(
                            label="Price Positioning",
                            choices=["budget", "mid-range", "premium", "luxury"],
                            value="premium"
                        )
                        usps = gr.Textbox(
                            label="Unique Selling Propositions (comma-separated)",
                            placeholder="First fully recycled smart bottle, AI-powered coaching",
                            value="First fully recycled smart water bottle, AI-powered hydration coaching, Carbon-neutral manufacturing"
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 👥 Target Demographics")
                        with gr.Row():
                            age_min = gr.Number(
                                label="Minimum Age",
                                value=25,
                                minimum=13,
                                maximum=100
                            )
                            age_max = gr.Number(
                                label="Maximum Age",
                                value=45,
                                minimum=13,
                                maximum=100
                            )
                        
                        with gr.Row():
                            income_level = gr.Dropdown(
                                label="Income Level",
                                choices=["low", "medium", "high", "luxury"],
                                value="high"
                            )
                            education_level = gr.Dropdown(
                                label="Education Level",
                                choices=["high-school", "college", "graduate", "mixed"],
                                value="college"
                            )
                        
                        locations = gr.Textbox(
                            label="Target Locations (comma-separated)",
                            placeholder="United States, Canada, Western Europe",
                            value="United States, Canada, Western Europe"
                        )
                        interests = gr.Textbox(
                            label="Target Interests (comma-separated)",
                            placeholder="fitness, sustainability, technology",
                            value="fitness, sustainability, technology, wellness"
                        )
                        values = gr.Textbox(
                            label="Target Values (comma-separated)",
                            placeholder="environmental responsibility, health consciousness",
                            value="environmental responsibility, health consciousness, innovation"
                        )
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🎯 Campaign Objectives")
                        objectives = gr.CheckboxGroup(
                            label="Select Objectives",
                            choices=["awareness", "conversion", "retention", "engagement"],
                            value=["awareness", "conversion"]
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📱 Target Platforms")
                        platforms = gr.CheckboxGroup(
                            label="Select Platforms",
                            choices=["facebook", "instagram", "twitter", "linkedin", "google_ads", "email", "website", "print"],
                            value=["instagram", "facebook", "google_ads", "website"]
                        )
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 📋 Additional Information (Optional)")
                        budget_range = gr.Textbox(
                            label="Budget Range",
                            placeholder="e.g., $50,000 - $100,000",
                            value="$50,000 - $100,000"
                        )
                        timeline = gr.Textbox(
                            label="Timeline",
                            placeholder="e.g., 6 weeks",
                            value="6 weeks"
                        )
                        additional_context = gr.Textbox(
                            label="Additional Context",
                            placeholder="Any additional information...",
                            lines=2,
                            value="Launching during Earth Day season to maximize environmental messaging impact"
                        )
                
                generate_btn = gr.Button(
                    "🚀 Generate Campaign",
                    variant="primary",
                    size="lg"
                )
        
        # Status output outside of tabs for better visibility
        status_output = gr.Textbox(
            label="🔄 Generation Status",
            interactive=False,
            lines=2
        )
        
        with gr.Tabs():
            with gr.Tab("📊 Campaign Results"):
                
                with gr.Tabs():
                    with gr.Tab("📝 Headlines & Taglines"):
                        headlines_output = gr.Textbox(
                            label="Generated Headlines",
                            lines=8,
                            interactive=False
                        )
                        taglines_output = gr.Textbox(
                            label="Generated Taglines",
                            lines=5,
                            interactive=False
                        )
                    
                    with gr.Tab("📢 Ad Copy"):
                        ad_copy_output = gr.Textbox(
                            label="Platform-Specific Ad Copy",
                            lines=15,
                            interactive=False
                        )
                    
                    with gr.Tab("🎨 Brand Elements"):
                        brand_output = gr.Textbox(
                            label="Brand Colors, Typography & Style",
                            lines=20,
                            interactive=False
                        )
                    
                    with gr.Tab("📄 Product Descriptions"):
                        descriptions_output = gr.Textbox(
                            label="Product Descriptions (Short, Medium, Long)",
                            lines=15,
                            interactive=False
                        )
                    
                    with gr.Tab("📋 Summary & Recommendations"):
                        summary_output = gr.Textbox(
                            label="Campaign Summary & Strategic Recommendations",
                            lines=15,
                            interactive=False
                        )
        
        # Connect the generate button to the function
        generate_btn.click(
            fn=generate_campaign_gradio,
            inputs=[
                product_name, product_category, product_description,
                key_features, price_point, usps,
                age_min, age_max, income_level, education_level,
                locations, interests, values,
                objectives, platforms,
                budget_range, timeline, additional_context
            ],
            outputs=[
                status_output, headlines_output, taglines_output,
                ad_copy_output, brand_output, descriptions_output, summary_output
            ]
        )
        
        gr.Markdown(
            """
            ---
            
            **💡 Tips:**
            - Fill out all required fields for best results
            - Use comma-separated lists for multiple items
            - Be specific about your target audience and product features
            - Campaign generation takes 2-4 minutes depending on complexity
            
            **🔑 API Usage:**
            - Ensure your OpenAI API key is set in the environment
            - Each campaign generation costs approximately $0.50-1.00
            - Text generation uses GPT-4, image generation uses DALL-E 3
            """
        )
    
    return interface


def main():
    """Main function to launch the Gradio app"""
    print("🚀 OpenAI Brand Campaign Agent - Gradio Interface")
    print("=" * 60)
    
    # Load environment and check API key
    api_key = load_environment()
    if not api_key:
        return
    
    # Create and launch interface
    print("🎨 Creating Gradio interface...")
    interface = create_gradio_interface(api_key)
    
    print("🌐 Launching web interface...")
    print("📋 Pre-filled with example data for EcoSmart Water Bottle")
    print("✏️ Modify the inputs as needed and click 'Generate Campaign'")
    print("⏱️ Campaign generation typically takes 2-4 minutes")
    print("\n" + "=" * 60)
    
    interface.launch(
        share=True,  # Creates a public link
        server_name="0.0.0.0",  # Allow external access
        server_port=7865,  # Use available port
        show_error=True
    )


if __name__ == "__main__":
    main()

