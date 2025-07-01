"""
OpenAI API client wrapper for the Brand Campaign Agent
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .models import (
    CampaignBrief, TextContent, ColorPalette, TypographyGuide, 
    BrandElements, GenerationConfig, PlatformType
)


class OpenAIClient:
    """Wrapper for OpenAI API interactions"""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
    
    def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using GPT model"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_text,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Text generation failed: {str(e)}")
    
    def generate_image(self, prompt: str, filename: str) -> str:
        """Generate image using DALL-E"""
        if not self.config.enable_image_generation:
            return ""
        
        try:
            response = self.client.images.generate(
                model=self.config.model_image,
                prompt=prompt,
                size=self.config.image_size,
                quality=self.config.image_quality,
                n=1
            )
            
            # Download and save the image
            import requests
            from PIL import Image
            import io
            
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image = Image.open(io.BytesIO(image_response.content))
            
            filepath = os.path.join(self.config.output_directory, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            image.save(filepath)
            
            return filepath
        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")


class CampaignGenerator:
    """Main campaign generation engine"""
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.openai_client = OpenAIClient(config)
    
    def generate_headlines(self, brief: CampaignBrief) -> List[str]:
        """Generate campaign headlines"""
        prompt = f"""
        Create {self.config.max_headlines} compelling headlines for a {brief.product_info.category} campaign.
        
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
        return headlines[:self.config.max_headlines]
    
    def generate_taglines(self, brief: CampaignBrief) -> List[str]:
        """Generate brand taglines"""
        prompt = f"""
        Create {self.config.max_taglines} memorable taglines for {brief.product_info.name}.
        
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
        return taglines[:self.config.max_taglines]
    
    def generate_ad_copy(self, brief: CampaignBrief) -> Dict[str, List[str]]:
        """Generate platform-specific ad copy"""
        ad_copy = {}
        
        for platform in brief.platforms:
            prompt = f"""
            Create {self.config.max_ad_copy_variants} ad copy variants for {platform.value}.
            
            Product: {brief.product_info.name}
            Category: {brief.product_info.category}
            Key Features: {', '.join(brief.product_info.key_features)}
            Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
            
            Platform-specific requirements for {platform.value}:
            {self._get_platform_requirements(platform)}
            
            Each variant should:
            - Hook the reader immediately
            - Highlight key benefits
            - Include a strong call-to-action
            - Match the platform's tone and format
            
            Return each variant separated by "---"
            """
            
            response = self.openai_client.generate_text(prompt)
            variants = [variant.strip() for variant in response.split('---') if variant.strip()]
            ad_copy[platform.value] = variants[:self.config.max_ad_copy_variants]
        
        return ad_copy
    
    def generate_product_descriptions(self, brief: CampaignBrief) -> List[str]:
        """Generate compelling product descriptions"""
        prompt = f"""
        Create 3 product description variants for {brief.product_info.name}.
        
        Product Details:
        - Category: {brief.product_info.category}
        - Features: {', '.join(brief.product_info.key_features)}
        - USPs: {', '.join(brief.product_info.unique_selling_propositions)}
        - Price Point: {brief.product_info.price_point}
        
        Target Audience Values: {', '.join(brief.demographics.values)}
        
        Create:
        1. Short description (50-75 words) - for product listings
        2. Medium description (100-150 words) - for product pages
        3. Long description (200-250 words) - for detailed marketing
        
        Each should be persuasive, benefit-focused, and appeal to the target audience.
        Separate each description with "---"
        """
        
        response = self.openai_client.generate_text(prompt)
        descriptions = [desc.strip() for desc in response.split('---') if desc.strip()]
        return descriptions
    
    def generate_call_to_actions(self, brief: CampaignBrief) -> List[str]:
        """Generate call-to-action phrases"""
        prompt = f"""
        Create 8 compelling call-to-action phrases for {brief.product_info.name}.
        
        Campaign Objectives: {', '.join([obj.value for obj in brief.objectives])}
        Target Audience Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
        Product Category: {brief.product_info.category}
        
        Include CTAs for:
        - Purchase/conversion
        - Learning more
        - Signing up
        - Engagement actions
        
        Make them action-oriented, urgent, and appealing to the target demographic.
        Return one CTA per line.
        """
        
        response = self.openai_client.generate_text(prompt)
        ctas = [line.strip() for line in response.split('\n') if line.strip()]
        return ctas
    
    def generate_social_media_posts(self, brief: CampaignBrief) -> Dict[str, List[str]]:
        """Generate social media content"""
        social_platforms = [p for p in brief.platforms if p in [
            PlatformType.FACEBOOK, PlatformType.INSTAGRAM, 
            PlatformType.TWITTER, PlatformType.LINKEDIN
        ]]
        
        social_content = {}
        
        for platform in social_platforms:
            prompt = f"""
            Create 3 social media posts for {platform.value} promoting {brief.product_info.name}.
            
            Product: {brief.product_info.name}
            Key Features: {', '.join(brief.product_info.key_features[:3])}
            Target Age: {brief.demographics.age_range[0]}-{brief.demographics.age_range[1]}
            
            Platform guidelines for {platform.value}:
            {self._get_social_platform_guidelines(platform)}
            
            Each post should:
            - Be platform-appropriate in tone and length
            - Include relevant hashtags
            - Have engaging hooks
            - Encourage interaction
            
            Separate posts with "---"
            """
            
            response = self.openai_client.generate_text(prompt)
            posts = [post.strip() for post in response.split('---') if post.strip()]
            social_content[platform.value] = posts
        
        return social_content
    
    def generate_color_palette(self, brief: CampaignBrief) -> ColorPalette:
        """Generate brand color palette"""
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
            # Fallback if JSON parsing fails
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
        """Generate typography recommendations"""
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
            # Fallback if JSON parsing fails
            return TypographyGuide(
                primary_font="Inter",
                secondary_font="Merriweather",
                heading_style="Bold, modern sans-serif for impact",
                body_style="Clean, readable serif for trust",
                font_pairing_rationale="Modern sans-serif paired with classic serif for balance"
            )
    
    def generate_complete_campaign(self, brief: CampaignBrief) -> TextContent:
        """Generate complete text content for campaign"""
        print("Generating headlines...")
        headlines = self.generate_headlines(brief)
        
        print("Generating taglines...")
        taglines = self.generate_taglines(brief)
        
        print("Generating ad copy...")
        ad_copy = self.generate_ad_copy(brief)
        
        print("Generating product descriptions...")
        product_descriptions = self.generate_product_descriptions(brief)
        
        print("Generating call-to-actions...")
        call_to_actions = self.generate_call_to_actions(brief)
        
        print("Generating social media content...")
        social_media_posts = self.generate_social_media_posts(brief)
        
        return TextContent(
            headlines=headlines,
            taglines=taglines,
            ad_copy=ad_copy,
            product_descriptions=product_descriptions,
            call_to_actions=call_to_actions,
            social_media_posts=social_media_posts
        )
    
    def _get_platform_requirements(self, platform: PlatformType) -> str:
        """Get platform-specific requirements"""
        requirements = {
            PlatformType.FACEBOOK: "- Conversational tone\n- 125 characters or less\n- Focus on community and sharing",
            PlatformType.INSTAGRAM: "- Visual-first approach\n- Lifestyle-focused\n- Use relevant hashtags",
            PlatformType.TWITTER: "- Concise and punchy\n- 280 characters max\n- Trending topics awareness",
            PlatformType.LINKEDIN: "- Professional tone\n- Business value focus\n- Industry expertise",
            PlatformType.GOOGLE_ADS: "- Clear value proposition\n- Strong CTA\n- Keyword optimization",
            PlatformType.EMAIL: "- Personal tone\n- Subject line optimization\n- Clear hierarchy",
            PlatformType.PRINT: "- Traditional advertising\n- Clear hierarchy\n- Brand prominence",
            PlatformType.WEBSITE: "- SEO-friendly\n- Conversion-focused\n- User experience priority"
        }
        return requirements.get(platform, "Standard advertising copy requirements")
    
    def _get_social_platform_guidelines(self, platform: PlatformType) -> str:
        """Get social media platform guidelines"""
        guidelines = {
            PlatformType.FACEBOOK: "- 40-80 characters for posts\n- Ask questions to encourage engagement\n- Use 1-2 hashtags max",
            PlatformType.INSTAGRAM: "- 138-150 characters optimal\n- Use 5-10 relevant hashtags\n- Include emoji for personality",
            PlatformType.TWITTER: "- 71-100 characters for retweets\n- Use 1-2 hashtags\n- Include mentions when relevant",
            PlatformType.LINKEDIN: "- 150-300 characters\n- Professional tone\n- Industry-specific hashtags"
        }
        return guidelines.get(platform, "Standard social media guidelines")

