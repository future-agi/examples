"""
Gradio Interface for Text-to-SQL Agent

This module provides a user-friendly Gradio interface for interacting with the text-to-SQL agent.
"""

import os
import logging
import gradio as gr
import pandas as pd
import base64
from io import BytesIO
from PIL import Image
from typing import Dict, List, Tuple, Optional, Any
import json
import time

from src.models.text2sql_agent import create_agent, Text2SQLAgent, AgentConfig


class GradioInterface:
    """Gradio interface for the Text-to-SQL agent"""
    
    def __init__(self):
        """Initialize the Gradio interface"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize the agent
        self.agent = self._create_agent()
        
        # Query history
        self.query_history: List[Dict[str, Any]] = []
        
        # Example questions
        self.example_questions = self._load_example_questions()
        
        self.logger.info("Gradio interface initialized")
    
    def _create_agent(self) -> Text2SQLAgent:
        """Create and configure the Text-to-SQL agent"""
        try:
            config = AgentConfig(
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                bigquery_project_id=os.getenv('GOOGLE_CLOUD_PROJECT', 'revionics-demo'),
                bigquery_dataset_id=os.getenv('BIGQUERY_DATASET', 'retail_analytics'),
                bigquery_credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
                vector_store_path=os.getenv('VECTOR_STORE_PATH', './chroma_db'),
                enable_cache=True,
                max_results=1000,
                enable_visualization=True,
                log_level='INFO'
            )
            
            agent = Text2SQLAgent(config)
            self.logger.info("Text-to-SQL agent created successfully")
            return agent
            
        except Exception as e:
            self.logger.error(f"Error creating agent: {str(e)}")
            raise
    
    def _load_example_questions(self) -> Dict[str, List[str]]:
        """Load example questions by category"""
        return {
            "Pricing Analysis": [
                "What is the current price for UPC code '0020282000000'?",
                "Show me pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'",
                "What are the factors driving the suggested price for items in price family '7286'?",
                "List items with the highest units impact from suggested prices for the week ending '2025-04-15'"
            ],
            "Elasticity Analysis": [
                "Show me the top 10 items by elasticity in the frozen food category",
                "Which products are candidates for price reductions due to high elasticity?",
                "What items should I decrease the price on to drive units in zone 'Orange'?",
                "Which items have changed elasticity the most in the last 12 weeks?"
            ],
            "Competitive Analysis": [
                "Which items have a CPI value higher than 1.05?",
                "List articles where Walmart prices are higher than No Frills Ontario prices",
                "What is the competitive price index for each subcategory under grocery?",
                "Which competitor had the highest number of price increases in April 2025?"
            ],
            "Sales & Performance": [
                "Show me the top 10 selling items within frozen food",
                "What are the top 10 items by forecast sales within the bakery category?",
                "Show me revenue by level 2 for the last 6 months in the POKE category",
                "Which products have the highest selling units within frozen food?"
            ],
            "Margin Analysis": [
                "Show me the bottom 10 lowest margin items in April",
                "Show me all items with negative margin in the last 7 days",
                "What is the impact on margin if I create a minimum price gap of 1% on 'C' products?",
                "Show me items with the lowest margin percentage"
            ]
        }
    
    def process_question(self, question: str, history: List[List[str]]) -> Tuple[str, List[List[str]], str, str, str, str]:
        """
        Process a user question and return formatted results
        
        Args:
            question: User's natural language question
            history: Chat history
            
        Returns:
            Tuple of (response, updated_history, sql_query, data_table, insights, visualization)
        """
        if not question.strip():
            return "", history, "", "", "", ""
        
        try:
            # Add user question to history
            history.append([question, "Processing..."])
            
            # Process the question
            start_time = time.time()
            response = self.agent.process_question(question)
            execution_time = time.time() - start_time
            
            # Format the response
            if response.success:
                # Create formatted response
                formatted_response = self._format_response(response)
                
                # Update history with the response
                history[-1][1] = formatted_response
                
                # Store in query history
                self.query_history.append({
                    'question': question,
                    'response': response,
                    'timestamp': time.time()
                })
                
                # Format outputs
                sql_output = f"```sql\n{response.sql_query}\n```"
                data_table = response.data_table or "No data to display"
                insights = self._format_insights(response.key_insights)
                visualization = self._format_visualization(response.visualization)
                
                return "", history, sql_output, data_table, insights, visualization
                
            else:
                # Handle error
                error_message = f"❌ **Error**: {response.error_message}"
                history[-1][1] = error_message
                
                return "", history, "", "", "", ""
                
        except Exception as e:
            self.logger.error(f"Error processing question: {str(e)}")
            error_message = f"❌ **System Error**: {str(e)}"
            
            if history and len(history) > 0:
                history[-1][1] = error_message
            else:
                history.append([question, error_message])
            
            return "", history, "", "", "", ""
    
    def _format_response(self, response) -> str:
        """Format the agent response for display"""
        formatted_parts = []
        
        # Main response
        formatted_parts.append(f"✅ **Answer**: {response.natural_language_response}")
        
        # Execution details
        formatted_parts.append(f"⏱️ **Execution Time**: {response.execution_time:.2f} seconds")
        formatted_parts.append(f"📊 **Rows Retrieved**: {response.row_count:,}")
        formatted_parts.append(f"🎯 **Confidence**: {response.confidence_score:.1%}")
        
        # Cache status
        if response.metadata.get('query_result_metadata', {}).get('cache_hit'):
            formatted_parts.append("💾 **Cache**: Hit (faster response)")
        
        return "\n\n".join(formatted_parts)
    
    def _format_insights(self, insights: List[str]) -> str:
        """Format key insights for display"""
        if not insights:
            return "No specific insights available."
        
        formatted_insights = []
        for i, insight in enumerate(insights, 1):
            formatted_insights.append(f"{i}. {insight}")
        
        return "\n".join(formatted_insights)
    
    def _format_visualization(self, visualization: Optional[str]) -> Optional[Image.Image]:
        """Format visualization for display"""
        if not visualization:
            return None
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(visualization)
            image = Image.open(BytesIO(image_data))
            return image
        except Exception as e:
            self.logger.error(f"Error formatting visualization: {str(e)}")
            return None
    
    def get_example_question(self, category: str) -> str:
        """Get a random example question from the selected category"""
        if category in self.example_questions:
            import random
            return random.choice(self.example_questions[category])
        return ""
    
    def get_agent_stats(self) -> str:
        """Get formatted agent statistics"""
        try:
            stats = self.agent.get_stats()
            
            formatted_stats = [
                f"**Total Queries**: {stats['total_queries']}",
                f"**Successful Queries**: {stats['successful_queries']}",
                f"**Success Rate**: {stats['success_rate']:.1%}",
                f"**Average Execution Time**: {stats['average_execution_time']:.2f}s"
            ]
            
            # BigQuery stats
            bq_stats = stats.get('bigquery_stats', {})
            if bq_stats:
                formatted_stats.extend([
                    "",
                    "**BigQuery Statistics**:",
                    f"- Cache Hit Rate: {bq_stats.get('cache_hit_rate', 0):.1%}",
                    f"- Total Bytes Processed: {bq_stats.get('total_bytes_processed', 0):,}",
                    f"- Total Bytes Billed: {bq_stats.get('total_bytes_billed', 0):,}"
                ])
            
            # Vector store stats
            vs_stats = stats.get('vector_store_stats', {})
            if vs_stats:
                formatted_stats.extend([
                    "",
                    "**Knowledge Base Statistics**:",
                    f"- Schemas: {vs_stats.get('schemas', 0)}",
                    f"- Examples: {vs_stats.get('examples', 0)}",
                    f"- Rules: {vs_stats.get('rules', 0)}"
                ])
            
            return "\n".join(formatted_stats)
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return f"Error retrieving statistics: {str(e)}"
    
    def get_health_status(self) -> str:
        """Get formatted health status"""
        try:
            health = self.agent.health_check()
            
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌'
            }
            
            overall_status = health['overall_status']
            formatted_health = [
                f"**Overall Status**: {status_emoji.get(overall_status, '❓')} {overall_status.title()}"
            ]
            
            # Component status
            for component, status in health['components'].items():
                component_status = status['status']
                emoji = status_emoji.get(component_status, '❓')
                formatted_health.append(f"**{component.title()}**: {emoji} {component_status.title()}")
                
                if component_status == 'unhealthy' and 'error' in status:
                    formatted_health.append(f"  - Error: {status['error']}")
            
            formatted_health.append(f"\n**Last Check**: {health.get('timestamp', 'Unknown')}")
            
            return "\n".join(formatted_health)
            
        except Exception as e:
            self.logger.error(f"Error getting health status: {str(e)}")
            return f"❌ Error retrieving health status: {str(e)}"
    
    def clear_cache(self) -> str:
        """Clear agent cache"""
        try:
            self.agent.clear_cache()
            return "✅ Cache cleared successfully"
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return f"❌ Error clearing cache: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        
        # Custom CSS for better styling
        custom_css = """
        .gradio-container {
            max-width: 1200px !important;
        }
        .chat-message {
            padding: 10px;
            margin: 5px 0;
            border-radius: 10px;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 20%;
        }
        .bot-message {
            background-color: #f5f5f5;
            margin-right: 20%;
        }
        .sql-code {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 10px;
            font-family: 'Courier New', monospace;
        }
        """
        
        with gr.Blocks(
            title="Text-to-SQL Agent",
            theme=gr.themes.Soft(),
            css=custom_css
        ) as interface:
            
            # Header
            gr.Markdown("""
            # 🏪 Text-to-SQL Agent
            
            Ask questions about your retail data in natural language and get instant insights with SQL queries and visualizations.
            
            **Examples**: *"What is the current price for UPC code '123456'?"* or *"Show me the top 10 items by elasticity"*
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Main chat interface
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=400,
                        show_label=True,
                        container=True
                    )
                    
                    with gr.Row():
                        question_input = gr.Textbox(
                            label="Ask a question about your retail data",
                            placeholder="e.g., What is the current price for UPC code '0020282000000'?",
                            lines=2,
                            scale=4
                        )
                        submit_btn = gr.Button("Submit", variant="primary", scale=1)
                    
                    # Example questions
                    with gr.Row():
                        category_dropdown = gr.Dropdown(
                            choices=list(self.example_questions.keys()),
                            label="Example Categories",
                            value="Pricing Analysis",
                            scale=2
                        )
                        example_btn = gr.Button("Get Example", scale=1)
                
                with gr.Column(scale=1):
                    # System status
                    with gr.Accordion("System Status", open=False):
                        health_status = gr.Markdown(
                            value=self.get_health_status(),
                            label="Health Status"
                        )
                        refresh_health_btn = gr.Button("Refresh Health", size="sm")
                    
                    # Statistics
                    with gr.Accordion("Statistics", open=False):
                        stats_display = gr.Markdown(
                            value=self.get_agent_stats(),
                            label="Agent Statistics"
                        )
                        refresh_stats_btn = gr.Button("Refresh Stats", size="sm")
                    
                    # Cache management
                    with gr.Accordion("Cache Management", open=False):
                        cache_status = gr.Markdown("Cache operations")
                        clear_cache_btn = gr.Button("Clear Cache", size="sm")
            
            # Results tabs
            with gr.Tabs():
                with gr.TabItem("SQL Query"):
                    sql_output = gr.Code(
                        label="Generated SQL Query",
                        language="sql",
                        lines=10
                    )
                
                with gr.TabItem("Data Table"):
                    data_table = gr.HTML(
                        label="Query Results",
                        value="No data to display"
                    )
                
                with gr.TabItem("Key Insights"):
                    insights_output = gr.Markdown(
                        label="Key Insights",
                        value="No insights available"
                    )
                
                with gr.TabItem("Visualization"):
                    visualization_output = gr.Image(
                        label="Data Visualization",
                        type="pil"
                    )
            
            # Event handlers
            def submit_question(question, history):
                return self.process_question(question, history)
            
            def get_example(category):
                return self.get_example_question(category)
            
            def refresh_health():
                return self.get_health_status()
            
            def refresh_stats():
                return self.get_agent_stats()
            
            def clear_cache_action():
                return self.clear_cache()
            
            # Wire up events
            submit_btn.click(
                fn=submit_question,
                inputs=[question_input, chatbot],
                outputs=[question_input, chatbot, sql_output, data_table, insights_output, visualization_output]
            )
            
            question_input.submit(
                fn=submit_question,
                inputs=[question_input, chatbot],
                outputs=[question_input, chatbot, sql_output, data_table, insights_output, visualization_output]
            )
            
            example_btn.click(
                fn=get_example,
                inputs=[category_dropdown],
                outputs=[question_input]
            )
            
            refresh_health_btn.click(
                fn=refresh_health,
                outputs=[health_status]
            )
            
            refresh_stats_btn.click(
                fn=refresh_stats,
                outputs=[stats_display]
            )
            
            clear_cache_btn.click(
                fn=clear_cache_action,
                outputs=[cache_status]
            )
            
            # Footer
            gr.Markdown("""
            ---
            **Text-to-SQL Agent** - Powered by GPT-4o and BigQuery
            
            💡 **Tips**: 
            - Be specific with UPC codes, dates, and categories
            - Use quotes around specific values (e.g., 'Banner 2')
            - Ask follow-up questions to refine your analysis
            """)
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        interface = self.create_interface()
        
        # Default launch parameters
        launch_params = {
            'server_name': '0.0.0.0',
            'server_port': 7860,
            'share': False,
            'debug': False,
            'show_error': True
        }
        
        # Override with provided parameters
        launch_params.update(kwargs)
        
        self.logger.info(f"Launching Gradio interface on {launch_params['server_name']}:{launch_params['server_port']}")
        
        return interface.launch(**launch_params)


def create_gradio_interface() -> GradioInterface:
    """Factory function to create Gradio interface"""
    return GradioInterface()


# Main execution
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and launch interface
    gradio_interface = create_gradio_interface()
    gradio_interface.launch(
        share=False,
        debug=True,
        show_error=True
    )

