"""
Main application file for the AI Font Finder.
This application helps users find fonts based on their described needs using AI analysis.
"""

import json
import os
import gradio as gr
from dotenv import load_dotenv
import base64

# Create necessary files
def create_env_file():
    """Create a .env file if it doesn't exist."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write("# Add your OpenAI API key here\n")
            f.write("OPENAI_API_KEY=\n")

# Create .env file
create_env_file()

# Load environment variables
load_dotenv()

# Import components
from font_database import get_fonts_by_weights, get_all_emotions, get_all_occasions, FONT_DATABASE
from ai_prompt_processor import process_user_input


from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType
from traceai_openai import OpenAIInstrumentor

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="image_font_project",
)


OpenAIInstrumentor().instrument(tracer_provider=trace_provider)

from opentelemetry import trace

trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

def search_fonts(text_input, api_key=None):
    """
    Process user input and return font suggestions with images.
    
    Args:
        text_input (str): User input describing the purpose or occasion
        api_key (str, optional): OpenAI API key
        
    Returns:
        str: HTML formatted results with font suggestions and images
    """
    # Update API key if provided
    if api_key and api_key.strip():
        os.environ["OPENAI_API_KEY"] = api_key.strip()
    
    # Process user input to get emotion and occasion weights
    with tracer.start_as_current_span("process_user_input") as span:
        with tracer.start_as_current_span("process_user_input") as child:
            emotion_weights, occasion_weights = process_user_input(text_input)
        
        # Get font suggestions based on weights
        with tracer.start_as_current_span(
            name="Tool - specific tool",
            attributes={
                # Set these attributes prior to invoking the tool, in case the tool raises an exception
                **{
                    "fi.span.kind": "TOOL",
                    "input.value": {
                        "emotion_weights": emotion_weights,
                        "occasion_weights": occasion_weights
                    },
                    "message.tool_calls.0.tool_call.function.name": "get_fonts_by_weights"
                },
            },
        ) as tool_span:
            font_suggestions = get_fonts_by_weights(emotion_weights, occasion_weights, top_n=5)
            tool_span.set_attribute(
                "message.tool_calls.0.tool_call.function.output", json.dumps(font_suggestions)
            )
    
    # Format results as HTML
    results_html = "<div class='result-container'>"
    
    # Add analysis section
    results_html += "<h3>Analysis of Your Input:</h3>"
    results_html += "<p><strong>Text analyzed:</strong> " + text_input + "</p>"
    
    # Display emotion weights
    results_html += "<p><strong>Detected emotions:</strong> "
    emotion_tags = [f"<span style='background-color: rgba(66, 135, 245, {weight});"
                    f"padding: 2px 6px; border-radius: 10px; margin: 0 2px; color: white;'>"
                    f"{emotion} ({weight:.1f})</span>"
                    for emotion, weight in emotion_weights.items()]
    results_html += " ".join(emotion_tags) + "</p>"
    
    # Display occasion weights
    results_html += "<p><strong>Detected occasions:</strong> "
    occasion_tags = [f"<span style='background-color: rgba(245, 131, 66, {weight});"
                     f"padding: 2px 6px; border-radius: 10px; margin: 0 2px; color: white;'>"
                     f"{occasion} ({weight:.1f})</span>"
                     for occasion, weight in occasion_weights.items()]
    results_html += " ".join(occasion_tags) + "</p>"
    
    # Add font suggestions section
    results_html += "<h3>Suggested Fonts:</h3>"
    
    # Display each font suggestion with image
    for i, (font_name, score, font_data) in enumerate(font_suggestions, 1):
        # Get font data
        emotions = font_data.get("emotions", [])
        occasions = font_data.get("occasions", [])
        image_path = font_data.get("image_path", "")
        font_url = font_data.get("url", "")
        
        # Create font example with styling
        results_html += f"<div style='margin-bottom: 30px; padding: 20px; border-radius: 10px; background-color: {'#f0f7ff' if i % 2 == 0 else '#fff0f0'}; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>"
        results_html += f"<h4 style='margin: 0; font-size: 20px;'>{i}. {font_name} <span style='font-size: 14px; color: #666; margin-left: 10px;'>(Score: {score:.2f})</span></h4>"
        
        # Add font image
        if os.path.exists(image_path):
            # Convert image to base64 for embedding
            with open(image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
                results_html += f"<div style='margin: 15px 0;'><img src='data:image/png;base64,{img_data}' alt='{font_name} sample' style='max-width: 100%; border: 1px solid #ddd; border-radius: 5px;'/></div>"
        else:
            results_html += f"<div style='margin: 15px 0; padding: 20px; background-color: #f5f5f5; border-radius: 5px; text-align: center;'>Image not available for {font_name}</div>"
        
        # Add font URL
        if font_url:
            results_html += f"<div style='margin: 10px 0;'><a href='{font_url}' target='_blank' style='color: #0066cc; text-decoration: none;'>Download Font</a></div>"
        
        # Add tags
        results_html += "<div style='margin-top: 10px; font-size: 14px;'>"
        results_html += "<strong>Emotions:</strong> " + ", ".join(emotions) + "<br>"
        results_html += "<strong>Occasions:</strong> " + ", ".join(occasions)
        results_html += "</div>"
        results_html += "</div>"
    
    results_html += "</div>"
    return results_html

# CSS for styling the interface
custom_css = """
.result-container {
    margin-top: 20px;
    padding: 20px;
    border-radius: 10px;
    background-color: #f9f9f9;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
"""

# Create the Gradio interface
with gr.Blocks(css=custom_css) as app:
    gr.Markdown("# AI Font Finder")
    gr.Markdown("""
    Describe your purpose, occasion, or the feeling you want to convey, 
    and AI will suggest fonts that match your needs.
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="Describe your purpose or occasion",
                placeholder="Example: I need a font for a professional business presentation that conveys trust and authority.",
                lines=3
            )
        with gr.Column(scale=1):
            api_key = gr.Textbox(
                label="OpenAI API Key (optional)",
                placeholder="sk-...",
                type="password"
            )
    
    search_button = gr.Button("Find Fonts", variant="primary")
    
    output = gr.HTML(label="Results")
    
    # Example inputs
    gr.Examples(
        examples=[
            ["I need a font for a children's birthday party invitation that is fun and playful."],
            ["I'm designing a website for a luxury fashion brand that needs to look elegant and sophisticated."],
            ["I need a font for academic research papers that looks professional and serious."],
            ["I'm creating a poster for a rock concert that needs to be bold and attention-grabbing."],
            ["I need a font for a wedding invitation that feels romantic and elegant."]
        ],
        inputs=text_input
    )
    
    # Set up event handlers
    search_button.click(
        fn=search_fonts,
        inputs=[text_input, api_key],
        outputs=output
    )
    
    # Add information about the application
    gr.Markdown("""
    ## How it works
    
    1. Enter a description of your purpose, occasion, or the feeling you want to convey
    2. AI analyzes your text to identify relevant emotions and occasions
    3. The system matches these attributes with fonts in our database
    4. You receive font suggestions with real font images ranked by relevance
    
    ## About
    
    This application uses AI to analyze your text and match it with fonts based on emotional and occasion attributes.
    It helps you find the perfect font for your specific needs without having to browse through hundreds of options.
    The database includes over 200 open-source fonts with real sample images.
    """)

# Launch the app when run directly
if __name__ == "__main__":
    app.launch()
