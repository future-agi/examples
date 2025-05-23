# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import os
import gradio as gr
import openai
from PIL import Image
import io
import base64
import requests
import time
from gradio.themes import Soft
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType, FiSpanKindValues, SpanAttributes

# Set up OpenAI client
# In a production environment, use environment variables for API key
# For this demo, we'll prompt the user to enter their API key
openai_api_key = ""

from traceai_openai import OpenAIInstrumentor

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="image_generator_model",
)

OpenAIInstrumentor().instrument(tracer_provider=trace_provider)

# Create a single FITracer instance for manual spans
_futr_tracer = FITracer(trace_provider.get_tracer(__name__))

def setup_openai_client(api_key):
    """Initialize the OpenAI client with the provided API key."""
    openai.api_key = api_key
    return openai.Client(api_key=api_key)

def generate_font_prompt(description, variation_type="base"):
    """Generate a prompt for font generation based on user description and variation type."""
    variation_modifiers = {
        "base": "",
        "bold": "bold, strong, heavy weight",
        "italic": "italic, cursive, slanted",
        "decorative": "decorative, ornate, stylized",
        "minimalist": "minimalist, clean, simple"
    }
    
    modifier = variation_modifiers.get(variation_type, "")
    if modifier:
        full_description = f"{description}, {modifier}"
    else:
        full_description = description
    
    prompt = f"""Generate a {full_description} font style. 
    Show the complete alphabet (A-Z, a-z), numbers (0-9), 
    and the sample text "The quick brown fox jumps over the lazy dog" in this font style. 
    Create a clean, professional presentation with high contrast against a simple background. 
    The output should clearly show the font characteristics with no additional decorative elements.
    Make sure the text is centered and well-formatted, with clear visibility of each character."""
    
    return prompt

def generate_font_image(client, prompt):
    """Generate a font sample image using the OpenAI API and save it to the output folder with the prompt as filename."""
    import re
    try:
        with _futr_tracer.start_as_current_span(
            "OpenAI Image Generation",
            fi_span_kind=FiSpanKindValues.LLM,
        ) as span:
            # Add LLM attributes and input
            span.set_attributes({
                SpanAttributes.LLM_MODEL_NAME: "gpt-image-1",
                SpanAttributes.LLM_PROVIDER: "openai",
                SpanAttributes.LLM_PROMPTS: prompt,
                SpanAttributes.LLM_INVOCATION_PARAMETERS: str({
                    "model": "gpt-image-1",
                    "n": 1,
                    "size": "1024x1024",
                }),
                SpanAttributes.INPUT_VALUE: prompt,
            })
            response = client.images.generate(
                model="gpt-image-1",  # Use the latest model supporting 4o
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
            image_b64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes))

        # Save image with prompt as filename (sanitized)
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # Sanitize prompt for filename
        safe_prompt = re.sub(r'[^a-zA-Z0-9_\-]', '_', prompt)[:100]  # limit length
        filename = f"{safe_prompt}.png"
        filepath = os.path.join(output_dir, filename)
        image.save(filepath)

        return image, None
    except Exception as e:
        return None, f"Error generating image: {str(e)}"

def generate_font_variations(client, description, progress=None):
    """Generate multiple font variations based on a single description."""
    variation_types = ["base", "bold", "italic", "decorative", "minimalist"]
    results = []
    errors = []
    
    for i, variation_type in enumerate(variation_types):
        if progress is not None:
            progress(i/len(variation_types), f"Generating {variation_type} variation...")
        
        prompt = generate_font_prompt(description, variation_type)
        image, error = generate_font_image(client, prompt)
        
        if image:
            results.append(image)
        if error:
            errors.append(error)
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    if progress is not None:
        progress(1.0, "Complete!")
    
    return results, errors

def validate_api_key(api_key):
    """Validate the OpenAI API key by making a test request."""
    if not api_key or len(api_key.strip()) < 10:
        return False, "API key is too short or empty"
    
    try:
        client = openai.Client(api_key=api_key)
        # Make a minimal API call to test the key
        client.models.list()
        return True, "API key is valid"
    except Exception as e:
        return False, f"API key validation failed: {str(e)}"

def font_generator(api_key, description, progress=gr.Progress()):
    """Main function to generate font samples based on user description."""
    # Validate inputs
    if not description:
        return None, None, None, None, None, "Please enter a font description"
    
    # Validate API key
    is_valid, message = validate_api_key(api_key)
    if not is_valid:
        return None, None, None, None, None, message
    
    # Set up client
    client = setup_openai_client(api_key)
    
    # Generate font variations
    progress(0, "Starting font generation...")
    images, errors = generate_font_variations(client, description, progress)
    
    # Handle results
    if not images:
        return None, None, None, None, None, f"Failed to generate any font samples. Errors: {', '.join(errors)}"
    
    # Pad with None if we didn't get 5 images
    while len(images) < 5:
        images.append(None)
    
    return images[0], images[1], images[2], images[3], images[4], "Font samples generated successfully!"

# Create Gradio interface
with gr.Blocks(theme=Soft(primary_hue="blue")) as demo:
    gr.Markdown("# Font Generator")
    gr.Markdown("""
    ## Generate custom font samples based on your description
    
    Describe the occasion, purpose, or style of font you're looking for, and we'll generate 5 custom font samples for you.
    """)
    
    with gr.Row():
        with gr.Column():
            api_key_input = gr.Textbox(
                label="OpenAI API Key", 
                placeholder="Enter your OpenAI API key here...",
                type="password"
            )
            
            description_input = gr.Textbox(
                label="Font Description", 
                placeholder="E.g., 'Elegant wedding invitation font', 'Retro 80s arcade game title', 'Modern tech company logo'"
            )
            
            generate_button = gr.Button("Generate Font Samples", variant="primary")
            
            status_output = gr.Textbox(label="Status")
            
    with gr.Row():
        gr.Markdown("## Example Descriptions")
    
    with gr.Row():
        example_buttons = [
            gr.Button("Wedding Invitation"),
            gr.Button("Cyberpunk Game"),
            gr.Button("Business Card"),
            gr.Button("Children's Book"),
            gr.Button("Tech Startup")
        ]
    
    with gr.Row():
        gr.Markdown("## Your Custom Font Samples")
    
    with gr.Row():
        image_outputs = [
            gr.Image(label=f"Font Sample {i+1}") for i in range(5)
        ]
    
    # Set up example button clicks
    example_descriptions = [
        "Elegant wedding invitation font with romantic flourishes",
        "Futuristic cyberpunk game title font with neon glow effects",
        "Professional business card font that conveys trust and expertise",
        "Playful children's book font that is fun and easy to read",
        "Modern tech startup logo font that feels innovative and clean"
    ]
    
    # Define click handlers for each example button
    def create_click_handler(description):
        return lambda: description
    
    for button, desc in zip(example_buttons, example_descriptions):
        button.click(
            create_click_handler(desc),
            inputs=[],
            outputs=[description_input]
        )
    
    # Set up main generate button
    generate_button.click(
        font_generator,
        inputs=[api_key_input, description_input],
        outputs=image_outputs + [status_output]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(share=True)
