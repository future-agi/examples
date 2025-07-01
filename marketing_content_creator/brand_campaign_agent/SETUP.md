# Setup Guide - Brand Campaign Agent

This guide will help you set up and run the Brand Campaign Agent on your system.

## Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python --version  # Should be 3.11+
   ```

2. **OpenAI API Key**
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Create an API key in your dashboard
   - Ensure you have credits for GPT-4 and DALL-E usage

## Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd brand_campaign_agent
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

**Option A: Environment Variable**
```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

**Option B: .env File** (Recommended)
Create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 5. Verify Installation
```bash
python main.py config
```

You should see a configuration table if everything is set up correctly.

## First Campaign Generation

### Using Interactive Mode
```bash
python main.py generate
```

Follow the prompts to create your first campaign brief.

### Using Example Brief
```bash
# Generate example brief
python main.py example

# Use the example brief
python main.py generate --brief-file example_campaign_brief.json --interactive false
```

## Web Interface Setup

### 1. Navigate to Web UI Directory
```bash
cd campaign-web-ui
```

### 2. Install Node.js Dependencies
```bash
# Using npm
npm install

# Using yarn
yarn install

# Using pnpm
pnpm install
```

### 3. Start Development Server
```bash
# Using npm
npm run dev

# Using yarn
yarn dev

# Using pnpm
pnpm dev
```

### 4. Open Browser
Navigate to `http://localhost:5173` to access the web interface.

## Configuration Options

### Basic Configuration
Edit `config/config.yaml` to customize:

```yaml
# OpenAI Models
openai:
  model_text: "gpt-4o"          # or "gpt-3.5-turbo" for lower cost
  model_image: "gpt-image-1"      # or "dall-e-2" for lower cost
  temperature: 0.7             # Creativity level (0.0-1.0)

# Content Limits
content_limits:
  max_headlines: 5             # Number of headlines to generate
  max_taglines: 3              # Number of taglines to generate
  max_ad_copy_variants: 3      # Variants per platform

# Image Generation
image_generation:
  enabled: true                # Set to false to disable images
  size: "1024x1024"           # Image dimensions
  quality: "standard"          # "standard" or "hd"
```

### Cost Optimization
To reduce API costs:

1. **Use GPT-3.5-turbo instead of GPT-4**
   ```yaml
   openai:
     model_text: "gpt-3.5-turbo"
   ```

2. **Disable image generation for testing**
   ```yaml
   image_generation:
     enabled: false
   ```

3. **Reduce content variants**
   ```yaml
   content_limits:
     max_headlines: 3
     max_taglines: 2
     max_ad_copy_variants: 2
   ```

## Troubleshooting

### Common Issues

**1. "OPENAI_API_KEY environment variable not set"**
- Ensure your API key is properly set in environment variables or .env file
- Check that the .env file is in the project root directory
- Verify the API key format starts with "sk-"

**2. "API rate limit exceeded"**
- Wait a few minutes and try again
- Check your OpenAI usage limits in the dashboard
- Consider upgrading your OpenAI plan

**3. "Image generation failed"**
- Check your OpenAI credits balance
- Verify DALL-E access in your OpenAI account
- Try disabling image generation temporarily

**4. "Module not found" errors**
- Ensure you're in the correct directory
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that your virtual environment is activated

**5. Web interface won't start**
- Ensure Node.js is installed: `node --version`
- Try deleting `node_modules` and reinstalling: `rm -rf node_modules && npm install`
- Check if port 5173 is available

### Performance Issues

**Slow generation times:**
- Image generation takes 30-60 seconds per image
- Complete campaigns typically take 3-5 minutes
- Consider disabling images for faster testing

**High API costs:**
- Monitor usage in OpenAI dashboard
- Use GPT-3.5-turbo for development
- Disable image generation when not needed

### Getting Help

1. **Check the logs** - Error messages usually indicate the issue
2. **Review configuration** - Ensure all settings are correct
3. **Test with example brief** - Use provided examples to isolate issues
4. **Check OpenAI status** - Visit [OpenAI Status](https://status.openai.com/)

## Development Setup

### For Contributors

1. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt  # If available
   ```

2. **Run tests**
   ```bash
   python -m pytest tests/  # If tests are available
   ```

3. **Code formatting**
   ```bash
   black src/
   isort src/
   ```

### Project Structure
```
brand_campaign_agent/
├── src/                     # Core Python modules
│   ├── models.py           # Data models
│   ├── openai_client.py    # OpenAI API wrapper
│   ├── image_generator.py  # Image generation
│   ├── campaign_orchestrator.py  # Main orchestrator
│   └── cli.py              # Command line interface
├── config/                 # Configuration files
├── campaign-web-ui/        # React web interface
├── examples/               # Example campaign briefs
├── output/                 # Generated campaigns
└── docs/                   # Additional documentation
```

## Next Steps

1. **Generate your first campaign** using the interactive mode
2. **Explore the web interface** for a visual experience
3. **Customize configuration** based on your needs
4. **Review generated content** and iterate on your brief
5. **Integrate into your workflow** using the API or CLI

## Support

- **Documentation**: README.md and inline code comments
- **Examples**: Check the `examples/` directory
- **Issues**: Report problems via GitHub Issues
- **Community**: Join discussions in GitHub Discussions

---

**Ready to create amazing campaigns? Start with `python main.py generate`!**

