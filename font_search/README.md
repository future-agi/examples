# AI Font Finder - User Guide

## Overview
AI Font Finder is a Gradio application that helps you find the perfect font based on your specific needs. Simply describe the purpose, occasion, or feeling you want to convey, and the AI will suggest fonts that match your requirements with real sample images.

## Features
- Text-based font search using AI analysis
- Database of 200+ open-source fonts with sample images
- Emotion and occasion tagging for accurate font matching
- Visual display of font examples as images
- Direct links to download each font
- Detailed analysis of input text

## Requirements
- Python 3.6 or higher
- Required Python packages:
  - gradio
  - openai
  - python-dotenv
  - pillow
  - requests

## Installation

1. Clone or download the application files to your local machine.

2. Install the required dependencies:
```bash
pip install gradio openai python-dotenv pillow requests
```

3. (Optional) Set up your OpenAI API key:
   - Create a `.env` file in the application directory
   - Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`
   - Alternatively, you can provide your API key directly in the application interface

## Running the Application

1. Navigate to the application directory:
```bash
cd path/to/font_finder
```

2. Run the application:
```bash
python main.py
```

3. Open your web browser and go to:
```
http://127.0.0.1:7860
```

## How to Use

1. Enter a description of your purpose, occasion, or the feeling you want to convey in the text input field.
   - Example: "I need a font for a professional business presentation that conveys trust and authority."
   - Example: "I'm designing a wedding invitation that should feel elegant and romantic."

2. (Optional) Enter your OpenAI API key if you want to use your own account.

3. Click the "Find Fonts" button.

4. Review the results:
   - The analysis section shows which emotions and occasions were detected in your text
   - The suggested fonts section displays the top font recommendations with sample images
   - Each font suggestion includes download links and emotional/occasion tags

5. Try different descriptions to get varied font suggestions.

## How It Works

1. Your text input is analyzed by AI to identify relevant emotions and occasions
2. The system assigns weights to each emotion and occasion based on the analysis
3. These weights are used to search the font database and find the best matches
4. The fonts are ranked by relevance and displayed with sample images

## File Structure

- `main.py`: Main application file
- `font_database.py`: Comprehensive font database with 200+ fonts
- `ai_prompt_processor.py`: AI text analysis module
- `font_images/`: Directory containing sample images for all fonts
- `.env`: Environment file for storing API keys (create this yourself)

## Troubleshooting

- If you don't provide an OpenAI API key, the application will use a fallback method for text analysis, which may be less accurate.
- If the application fails to start, ensure all dependencies are installed correctly.
- If font images don't display, check that the font_images directory exists and contains the image files.
- For any issues with the OpenAI integration, check that your API key is valid and has sufficient credits.

## Credits

This application uses:
- Gradio for the web interface
- OpenAI for text analysis
- Google Fonts for the open-source font collection
- A curated database of fonts with emotional and occasion tagging
