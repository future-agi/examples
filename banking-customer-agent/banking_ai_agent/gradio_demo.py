#!/usr/bin/env python3
"""
Banking AI Agent - Gradio Demo Interface
A clean and user-friendly demo interface for testing the Banking AI Agent
"""

import gradio as gr
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Tuple, Optional

# Add the src directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.agent import BankingAIAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BankingAIGradioDemo:
    """Gradio demo interface for Banking AI Agent"""
    
    def __init__(self):
        self.agent = None
        self.conversation_history = []
        self.current_customer_id = "DEMO_USER"
        self.current_session_id = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the Banking AI Agent"""
        try:
            # Load environment variables from .env file
            from dotenv import load_dotenv
            load_dotenv()
            
            # Load configuration
            config = {
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'model_name': 'gpt-4o',
                'temperature': 0.1,
                'max_tokens': 1000,
                'chroma_db_path': './data/chroma_db',
                'memory_db_path': './data/memory.db',
                'log_level': 'INFO'
            }
            
            if not config['openai_api_key']:
                logger.error("OPENAI_API_KEY not found in environment variables")
                return
            
            # Initialize agent
            self.agent = BankingAIAgent(config)
            
            # The agent is already initialized with RAG system in the constructor
            # No need for separate initialize_rag_system call
            
            # Generate new session ID
            import uuid
            self.current_session_id = str(uuid.uuid4())[:8]
            
            logger.info("Banking AI Agent initialized successfully for Gradio demo")
            
        except Exception as e:
            logger.error(f"Failed to initialize Banking AI Agent: {str(e)}")
            self.agent = None
    
    def process_message(self, message: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
        """Process user message and return response"""
        if not self.agent:
            error_msg = "❌ Banking AI Agent is not initialized. Please check the configuration."
            history.append((message, error_msg))
            return "", history
        
        if not message.strip():
            return "", history
        
        try:
            # Process query with the agent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self.agent.process_query(
                query=message,
                customer_id=self.current_customer_id,
                session_id=self.current_session_id,
                context={}
            ))
            
            loop.close()
            
            # Format response with metadata
            response = result.content
            
            # Add confidence and compliance info
            metadata_info = []
            if hasattr(result, 'confidence') and result.confidence:
                confidence_pct = int(result.confidence * 100)
                metadata_info.append(f"🎯 Confidence: {confidence_pct}%")
            
            if hasattr(result, 'compliance_status') and result.compliance_status:
                if result.compliance_status == "compliant":
                    metadata_info.append("✅ Compliant")
                elif result.compliance_status == "warning":
                    metadata_info.append("⚠️ Compliance Warning")
                else:
                    metadata_info.append("❌ Compliance Issue")
            
            if metadata_info:
                response += f"\n\n*{' | '.join(metadata_info)}*"
            
            # Add to history
            history.append((message, response))
            
            return "", history
            
        except Exception as e:
            error_msg = f"❌ Error processing your request: {str(e)}"
            logger.error(f"Error in process_message: {str(e)}")
            history.append((message, error_msg))
            return "", history
    
    def get_account_balance(self, customer_id: str, account_id: str) -> str:
        """Get account balance for demo purposes"""
        if not self.agent:
            return "❌ Banking AI Agent is not initialized."
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.agent.tools_manager.get_account_balance(customer_id, account_id)
            )
            
            loop.close()
            
            if result.get('success'):
                return f"""✅ **Account Balance Retrieved**
                
**Account ID:** {result['account_id']}
**Account Type:** {result['account_type'].title()}
**Balance:** ${result['balance']:,.2f} {result['currency']}
**Available Balance:** ${result['available_balance']:,.2f} {result['currency']}
**Status:** {result['status'].title()}
**Last Transaction:** {result['last_transaction_date']}
"""
            else:
                return f"❌ {result.get('error', 'Unknown error occurred')}"
                
        except Exception as e:
            return f"❌ Error retrieving account balance: {str(e)}"
    
    def get_system_status(self) -> str:
        """Get system status for demo purposes"""
        if not self.agent:
            return "❌ Banking AI Agent is not initialized."
        
        try:
            status = self.agent.get_health_status()
            
            status_text = f"""🏦 **Banking AI Agent System Status**

**Overall Status:** {'✅ Healthy' if status['agent_status'] == 'healthy' else '❌ Issues Detected'}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Core Modules:**
• **Planning Module:** {'✅' if status['planning_module']['status'] == 'healthy' else '❌'} {status['planning_module']['status'].title()}
• **RAG System:** {'✅' if status['rag_system']['status'] == 'healthy' else '❌'} {status['rag_system']['status'].title()}
• **Memory System:** {'✅' if status['memory_system']['status'] == 'healthy' else '❌'} {status['memory_system']['status'].title()}
• **Compliance Checker:** {'✅' if status['compliance_checker']['status'] == 'healthy' else '❌'} {status['compliance_checker']['status'].title()}
• **Tools Manager:** {'✅' if status['tools_manager']['status'] == 'healthy' else '❌'} {status['tools_manager']['status'].title()}

**Knowledge Base:** {status['rag_system']['knowledge_base']['total_documents']} documents loaded
**Active Sessions:** {status['memory_system']['statistics']['active_sessions']}
**Total Customers:** {status['tools_manager']['statistics']['total_customers']}
"""
            return status_text
            
        except Exception as e:
            return f"❌ Error retrieving system status: {str(e)}"
    
    def clear_conversation(self) -> List[Tuple[str, str]]:
        """Clear conversation history"""
        # Generate new session ID
        import uuid
        self.current_session_id = str(uuid.uuid4())[:8]
        return []
    
    def create_interface(self):
        """Create the Gradio interface"""
        
        # Custom CSS for banking theme
        css = """
        .gradio-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .demo-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #2a5298;
            margin-bottom: 20px;
        }
        .status-box {
            background: #e8f4fd;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #bee5eb;
        }
        """
        
        with gr.Blocks(css=css, title="Banking AI Agent Demo") as demo:
            
            # Header
            gr.HTML("""
            <div class="header">
                <h1>🏦 Banking AI Agent Demo</h1>
                <p>Intelligent Customer Service Platform with Advanced AI Capabilities</p>
                <p><strong>Features:</strong> Planning • RAG • Execution • Memory • Self-Reflection • Complex Reasoning</p>
            </div>
            """)
            
            # Demo information
            gr.HTML("""
            <div class="demo-info">
                <h3>🎯 Demo Information</h3>
                <p><strong>Customer ID:</strong> DEMO_USER | <strong>Available Accounts:</strong> CHK001 (Checking), SAV001 (Savings)</p>
                <p><strong>Sample Queries:</strong> "What's my account balance?", "Transfer $500 to savings", "Tell me about your loan products"</p>
            </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Main chat interface
                    gr.Markdown("## 💬 Banking AI Assistant")
                    
                    chatbot = gr.Chatbot(
                        value=[("", "Hello! I'm your Banking AI Assistant. How can I help you today? 🏦")],
                        height=400,
                        show_label=False,
                        type="tuples"
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="Ask me about your accounts, transactions, or banking services...",
                            show_label=False,
                            scale=4
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)
                        clear_btn = gr.Button("Clear", variant="secondary", scale=1)
                
                with gr.Column(scale=1):
                    # Banking tools panel
                    gr.Markdown("## 🛠️ Banking Tools")
                    
                    with gr.Group():
                        gr.Markdown("### Account Balance")
                        customer_id_input = gr.Textbox(
                            value="CUST001",
                            label="Customer ID",
                            placeholder="Enter customer ID"
                        )
                        account_id_input = gr.Textbox(
                            value="CHK001",
                            label="Account ID", 
                            placeholder="Enter account ID"
                        )
                        balance_btn = gr.Button("Get Balance", variant="secondary")
                        balance_output = gr.Markdown()
                    
                    with gr.Group():
                        gr.Markdown("### System Status")
                        status_btn = gr.Button("Check Status", variant="secondary")
                        status_output = gr.Markdown()
            
            # Event handlers
            def respond(message, history):
                return self.process_message(message, history)
            
            # Chat interactions
            msg.submit(respond, [msg, chatbot], [msg, chatbot])
            send_btn.click(respond, [msg, chatbot], [msg, chatbot])
            clear_btn.click(self.clear_conversation, outputs=[chatbot])
            
            # Banking tools interactions
            balance_btn.click(
                self.get_account_balance,
                inputs=[customer_id_input, account_id_input],
                outputs=[balance_output]
            )
            
            status_btn.click(
                self.get_system_status,
                outputs=[status_output]
            )
            
            # Footer
            gr.HTML("""
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <p><strong>Banking AI Agent</strong> - Enterprise-Grade Intelligent Customer Service</p>
                <p>Powered by GPT-4o • Built for Major Financial Institutions</p>
            </div>
            """)
        
        return demo

def main():
    """Main function to run the Gradio demo"""
    print("🏦 Starting Banking AI Agent Gradio Demo...")
    
    # Initialize demo
    demo_app = BankingAIGradioDemo()
    
    # Create interface
    demo = demo_app.create_interface()
    
    # Launch demo
    print("🚀 Launching Gradio interface...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()

