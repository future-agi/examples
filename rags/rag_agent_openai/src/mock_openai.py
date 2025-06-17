"""
Mock OpenAI Module for Testing

This module provides mock implementations of OpenAI API calls for testing purposes.
"""

class MockChatCompletion:
    """Mock implementation of OpenAI chat completion"""
    
    @staticmethod
    def create(model, messages, temperature=0.7):
        """
        Mock implementation of chat completion create method
        
        Args:
            model: Model name (ignored in mock)
            messages: List of message dictionaries
            temperature: Temperature for generation (ignored in mock)
            
        Returns:
            Mock response object
        """
        # Extract the last user message
        user_message = None
        for message in reversed(messages):
            if message["role"] == "user":
                user_message = message["content"]
                break
        
        # Generate mock response based on user message
        response_content = ""
        
        if "break down" in user_message.lower():
            # Mock question breakdown
            if "RAG" in user_message or "retrieval" in user_message:
                response_content = "- What are the main components of RAG systems?\n- How do traditional deep learning approaches work?\n- What are the key differences between RAG systems and traditional deep learning?"
            elif "climate change" in user_message:
                response_content = "- What is climate change?\n- What causes climate change?\n- What are the effects of climate change on the environment?\n- What are the effects of climate change on human society?"
            else:
                response_content = "- What is the main question asking about?\n- What are the key components of the subject?\n- How does the subject compare to alternatives?"
        
        elif "RAG" in user_message or "retrieval" in user_message:
            # Mock RAG system response
            response_content = """
            RAG (Retrieval-Augmented Generation) systems combine retrieval mechanisms with generative models to produce more accurate and factual responses. The main components include:

            1. A knowledge base or document store that contains factual information
            2. A retrieval component that finds relevant documents based on the query
            3. A reranking mechanism that prioritizes the most relevant retrieved documents
            4. A generator that creates responses based on the retrieved context

            These systems differ from traditional deep learning approaches by grounding responses in retrieved information rather than relying solely on parameters learned during training. This helps reduce hallucinations and improves factual accuracy.
            """
        
        elif "reranking" in user_message:
            # Mock reranking explanation
            response_content = """
            The reranking process in RAG systems is a crucial step that improves retrieval precision. After initial retrieval, which typically uses embedding similarity to find potentially relevant documents, reranking applies a more sophisticated model to score these candidates.

            Rerankers often use cross-encoders that process the query and document together, allowing for more nuanced understanding of relevance compared to the initial retrieval step. This helps prioritize truly relevant information before passing it to the generation step.
            """
        
        else:
            # Generic mock response
            response_content = """
            Based on the information in the provided context, I can provide the following answer to your question.
            
            The topic you're asking about involves several key aspects that are important to understand. First, it's a complex system with multiple interacting components. Second, these components work together to achieve specific outcomes.
            
            For more detailed information, I would recommend consulting specialized resources on this topic.
            """
        
        # Create mock response object
        class MockResponse:
            class MockChoice:
                class MockMessage:
                    def __init__(self, content):
                        self.content = content
                
                def __init__(self, message):
                    self.message = message
            
            def __init__(self, choices):
                self.choices = choices
        
        return MockResponse([MockResponse.MockChoice(MockResponse.MockChoice.MockMessage(response_content.strip()))])

# Mock OpenAI module
class MockOpenAI:
    """Mock OpenAI module"""
    
    class Chat:
        """Mock chat module"""
        completions = MockChatCompletion()
    
    chat = Chat()

# Export mock module
mock_openai = MockOpenAI()
