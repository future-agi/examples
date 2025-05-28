# E-commerce Agent Documentation

## Overview

This e-commerce agent is a Gradio-based application that provides an interactive interface for users to perform various e-commerce operations. The agent can handle user queries with images, search for products, place orders, search for existing orders, cancel orders, and provide product recommendations with optional image rendering.

## Features

- **Natural Language Query Processing**: Process user queries in natural language
- **Image Input Support**: Accept and analyze user-provided images
- **Skill-based Architecture**: Modular design with specialized skills for different tasks
- **Task Planning**: Break down complex tasks into manageable steps
- **Memory System**: Store and retrieve information across interactions
- **Self-reflection**: Analyze actions and improve responses
- **Product Recommendations**: Generate product recommendations based on text and images
- **Image Rendering**: Visualize recommended products on user-provided images

## System Architecture

The system is built with a modular architecture consisting of the following components:

1. **Gradio Interface**: The user-facing interface for interaction
2. **Router**: Directs user queries to appropriate skills
3. **Skills**: Specialized modules for different e-commerce operations
4. **Memory**: Stores information across interactions
5. **Reflection**: Analyzes actions and suggests improvements
6. **Planner**: Breaks down complex tasks into steps
7. **Image Processor**: Analyzes images and generates renderings
8. **Product Recommender**: Provides product recommendations

## Module Descriptions

### Memory (`memory.py`)

The Memory module provides persistent storage for the agent's interactions and data. It allows adding entries with different types, retrieving all entries, filtering by type, and getting recent entries.

### Reflection (`reflection.py`)

The Reflection module enables the agent to analyze its actions and results, evaluate success, suggest improvements, and summarize insights. This helps the agent learn from past interactions and improve over time.

### Planner (`planner.py`)

The Planner module breaks down complex tasks into manageable steps. It creates plans based on task descriptions, updates step statuses, and tracks progress. Different task types have specialized step sequences.

### Router (`router.py`)

The Router module directs user queries to the appropriate skill based on keyword matching and scoring. It allows registering skills with associated keywords and routes queries to the best matching skill.

### Image Processor (`image_processor.py`)

The Image Processor module handles image analysis, product recommendation generation, and product rendering using OpenAI's vision and DALL-E capabilities.

### Product Recommender (`product_recommender.py`)

The Product Recommender module provides product recommendations based on user queries and images. It can also create visualizations of recommended products on user-provided images.

### E-commerce Skills (`main.py`)

The E-commerce Skills module implements specialized skills for different e-commerce operations:
- Search for products
- Place orders
- Search for orders
- Cancel orders
- Provide product recommendations

### E-commerce Agent (`main.py`)

The E-commerce Agent is the main class that integrates all components and provides the interface for processing user queries and managing conversations.

## Setup and Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ecom_agent/prototype 
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     FI_API_KEY=your_fi_api_key_here
     FI_SECRET_KEY=your_fi_secret_key_here
     ```


### Running the Application

Run the application using:
```
python run.py
```

### Running the Test Script

```
python prototype.py --scenario basic
```

This will start the Gradio interface, which will be accessible at `http://localhost:7860` by default.

## Usage Guide

### Basic Interaction

Type your query in the text input field and click "Submit" to interact with the agent. The agent will process your query and provide a response in the conversation area.

### Using Images

To include an image with your query:
1. Upload an image using the image upload field
2. Type your query in the text input field
3. Click "Submit"

### Example Queries

- "Search for blue shirts"
- "I want to buy a new laptop"
- "Find my order ORD-1001"
- "Cancel my order ORD-1002"
- "Recommend clothes that match this image"

### Product Recommendations with Image Rendering

When you ask for product recommendations with an image, the agent will:
1. Analyze your image
2. Generate product recommendations
3. Ask if you want to see a visualization of the recommended product on your image
4. If you respond "yes," create and display the visualization

## Testing

The application includes comprehensive test suites:

- `test_core.py`: Tests for core components (Memory, Reflection, Planner, Router)
- `test_image_features.py`: Tests for image processing features
- `test_integration.py`: Integration tests for skills and agent

Run tests using:
```
python -m unittest discover
```

## Deployment

The application can be deployed in several ways:

### Local Deployment

For local deployment, simply run:
```
python run.py
```

### Cloud Deployment

For cloud deployment, you can use services like:
- Hugging Face Spaces
- Heroku
- AWS
- Google Cloud

Follow these steps for deployment:
1. Ensure all dependencies are in `requirements.txt`
2. Set up environment variables in your cloud provider
3. Configure the deployment to run `run.py`

## Extending the Application

### Adding New Skills

To add a new skill:
1. Create a new method in the `EcommerceSkills` class in `main.py`
2. Register the skill with the router in the `EcommerceAgent.__init__` method
3. Implement the skill logic

### Customizing the Interface

The Gradio interface can be customized in the `create_interface` function in `main.py`.

## Troubleshooting

### Common Issues

- **OpenAI API Key**: Ensure your API key is correctly set in the `.env` file
- **Image Processing**: If image processing features don't work, check your OpenAI API key and subscription
- **Memory Usage**: For large conversations, consider clearing the conversation periodically

### Logging

The application logs important events and errors. Check the console output for any error messages.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Gradio for the interactive interface
- OpenAI for image processing capabilities


# Run a specific conversation dataset
python prototype.py --dataset shopping_journey

# Run all datasets
python prototype.py --all-datasets

# Run with custom delay and save results
python prototype.py --all-datasets --delay 2.0 --save-results

# Interactive mode
python prototype.py --interactive