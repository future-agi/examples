# Brand Campaign Agent

An AI-powered tool that generates comprehensive brand advertising campaigns using OpenAI's GPT-4 and DALL-E models. Create cohesive marketing materials including copy, visuals, and brand elements tailored to specific demographics and product information.

## 🚀 Features

### Content Generation
- **Headlines & Taglines**: Catchy, memorable phrases that capture brand essence
- **Ad Copy**: Platform-specific persuasive text for social media, print, and digital
- **Product Descriptions**: Compelling descriptions highlighting key benefits
- **Call-to-Actions**: Strategic CTAs optimized for target audience
- **Social Media Content**: Platform-optimized posts with appropriate tone and hashtags

### Visual Asset Creation
- **Hero Images**: Primary campaign visuals using DALL-E
- **Product Mockups**: Contextual product placement images
- **Social Media Assets**: Platform-specific image formats
- **Supporting Graphics**: Background patterns and icon sets

### Brand Element Generation
- **Color Palettes**: Psychologically-informed color schemes with hex codes
- **Typography Guides**: Font recommendations with pairing rationale
- **Logo Concepts**: Detailed logo descriptions and variations
- **Brand Guidelines**: Comprehensive style guide with usage recommendations
- **Visual Style Direction**: Overall aesthetic and design principles

### Audience-Specific Customization
- **Demographic Analysis**: Age, gender, income, location considerations
- **Psychographic Profiling**: Values, interests, lifestyle factors
- **Platform Optimization**: Content adapted for specific channels
- **Cultural Sensitivity**: Appropriate messaging for target markets

## 📋 Requirements

- Python 3.11+
- OpenAI API key
- Required Python packages (see `requirements.txt`)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd brand_campaign_agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ```

## 🚀 Quick Start

### Command Line Interface

1. **Interactive Mode** (Recommended for first-time users)
   ```bash
   python main.py generate
   ```
   This will guide you through creating a campaign brief step by step.

2. **Using a Brief File**
   ```bash
   # Generate example brief
   python main.py example
   
   # Use the example brief
   python main.py generate --brief-file example_campaign_brief.json --interactive false
   ```

3. **View Configuration**
   ```bash
   python main.py config
   ```

### Web Interface

1. **Navigate to the web UI directory**
   ```bash
   cd campaign-web-ui
   ```

2. **Install dependencies** (if not already done)
   ```bash
   yarn install
   # or
   npm install
   ```

3. **Start the development server**
   ```bash
   yarn dev
   # or
   npm run dev
   ```

4. **Open your browser** to `http://localhost:5173`

## 📖 Usage Examples

### Example 1: Tech Product Campaign

```json
{
  "product_info": {
    "name": "SmartFit Pro",
    "category": "fitness wearable",
    "description": "Advanced fitness tracker with AI-powered health insights",
    "key_features": ["Heart rate monitoring", "Sleep tracking", "AI coaching"],
    "price_point": "premium",
    "unique_selling_propositions": ["Most accurate heart rate sensor", "Personalized AI recommendations"]
  },
  "demographics": {
    "age_range": [25, 45],
    "income_level": "high",
    "geographic_location": ["United States", "Canada"],
    "education_level": "college",
    "interests": ["fitness", "technology", "health"],
    "values": ["health consciousness", "innovation", "quality"]
  },
  "objectives": ["awareness", "conversion"],
  "platforms": ["instagram", "facebook", "google_ads"]
}
```

### Example 2: Sustainable Fashion Campaign

```json
{
  "product_info": {
    "name": "EcoThreads",
    "category": "sustainable fashion",
    "description": "Ethically-made clothing from recycled materials",
    "key_features": ["100% recycled materials", "Fair trade certified", "Carbon neutral shipping"],
    "price_point": "mid-range",
    "unique_selling_propositions": ["First carbon-negative clothing line", "Transparent supply chain"]
  },
  "demographics": {
    "age_range": [22, 35],
    "income_level": "medium",
    "geographic_location": ["United States", "Europe"],
    "education_level": "college",
    "interests": ["sustainability", "fashion", "environment"],
    "values": ["environmental responsibility", "ethical consumption", "authenticity"]
  },
  "objectives": ["awareness", "engagement"],
  "platforms": ["instagram", "tiktok", "website"]
}
```

## 🔧 Configuration

The agent can be configured via `config/config.yaml`:

```yaml
# OpenAI API Settings
openai:
  model_text: "gpt-4o"
  model_image: "gpt-image-1"
  max_tokens: 2000
  temperature: 0.7

# Image Generation Settings
image_generation:
  enabled: true
  size: "1024x1024"
  quality: "standard"
  
# Content Generation Limits
content_limits:
  max_headlines: 5
  max_taglines: 3
  max_ad_copy_variants: 3

# Output Settings
output:
  directory: "./output"
  create_subdirectories: true
```

## 📁 Output Structure

Generated campaigns are saved in the following structure:

```
output/
└── campaign_{id}/
    ├── campaign_data.json          # Complete campaign data
    ├── campaign_summary.md         # Executive summary
    ├── text_content/
    │   ├── headlines.txt
    │   ├── taglines.txt
    │   ├── ad_copy_{platform}.txt
    │   ├── product_descriptions.txt
    │   ├── call_to_actions.txt
    │   └── social_posts_{platform}.txt
    ├── brand_elements/
    │   ├── color_palette.json
    │   ├── typography_guide.txt
    │   ├── logo_concepts.txt
    │   └── brand_guidelines.md
    └── visual_assets/
        ├── hero_images/
        ├── social_media/
        ├── product_mockups/
        └── supporting_graphics/
```

## 🎯 Use Cases

### Marketing Agencies
- Generate multiple campaign concepts for client presentations
- Create comprehensive brand packages for new clients
- Develop platform-specific content variations

### Startups & Small Businesses
- Launch new products with professional marketing materials
- Establish brand identity and visual guidelines
- Create cost-effective marketing campaigns

### E-commerce Brands
- Generate product-specific marketing content
- Create seasonal campaign variations
- Develop platform-optimized advertising materials

### Content Creators
- Develop brand partnerships and sponsored content
- Create consistent brand messaging across platforms
- Generate ideas for brand collaborations

## 🔌 API Integration

The agent can be integrated into existing workflows:

```python
from src import CampaignOrchestrator, GenerationConfig, CampaignBrief

# Initialize the orchestrator
config = GenerationConfig(
    openai_api_key="your-api-key",
    output_directory="./campaigns"
)
orchestrator = CampaignOrchestrator(config)

# Create campaign brief
brief = CampaignBrief(
    product_info=ProductInfo(...),
    demographics=Demographics(...),
    objectives=[...],
    platforms=[...]
)

# Generate campaign
campaign = orchestrator.generate_complete_campaign(brief)
```

## 🎨 Customization

### Custom Prompts
Modify prompt templates in the source code to adjust output style:
- `src/openai_client.py` - Text generation prompts
- `src/image_generator.py` - Image generation prompts

### Brand Templates
Create industry-specific templates by modifying:
- Color palette generation logic
- Typography recommendations
- Visual style guidelines

### Platform Extensions
Add new platforms by extending:
- `PlatformType` enum in `models.py`
- Platform-specific requirements in `openai_client.py`

## 🚨 Limitations

- **API Costs**: Image generation can be expensive for large campaigns
- **Generation Time**: Complete campaigns may take 3-5 minutes to generate
- **Content Quality**: Output quality depends on input brief quality
- **Image Accuracy**: DALL-E may not always generate perfect product representations

## 🔒 Privacy & Security

- API keys are stored locally and never transmitted except to OpenAI
- Generated content is saved locally by default
- No user data is collected or stored by the application
- All communications with OpenAI follow their privacy policies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions

## 🙏 Acknowledgments

- OpenAI for providing GPT-4 and DALL-E APIs
- The open-source community for the excellent libraries used
- Contributors and testers who helped improve the tool

## 📊 Roadmap

### Upcoming Features
- [ ] Video content generation
- [ ] Multi-language support
- [ ] Performance analytics integration
- [ ] Template marketplace
- [ ] Batch campaign generation
- [ ] A/B testing recommendations

### Integrations
- [ ] Adobe Creative Suite export
- [ ] Figma integration
- [ ] Social media scheduling tools
- [ ] CRM platform connections
- [ ] Analytics platform integration

---

**Made with ❤️ using OpenAI • [Documentation](docs/) • [Examples](examples/) • [API Reference](api/)**

