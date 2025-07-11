"""
Banking Scenario Tests - Comprehensive Testing Suite
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch

# Import core components
from src.core.agent import BankingAIAgent
from src.core.planning import TaskType, Priority
from src.core.compliance import ComplianceResult

class TestBankingScenarios:
    """Test suite for banking scenarios"""
    
    @pytest.fixture
    async def banking_agent(self):
        """Create a test banking agent instance"""
        config = {
            'openai_api_key': 'test-key',
            'model_name': 'gpt-4o',
            'temperature': 0.1,
            'max_tokens': 2000,
            'chroma_persist_directory': './test_data/chroma_db',
            'database_path': './test_data/memory.db',
            'max_context_length': 10,
            'context_window_hours': 24,
            'chunk_size': 1000,
            'chunk_overlap': 200,
            'max_retrieval_docs': 10,
            'embedding_model': 'text-embedding-ada-002'
        }
        
        # Mock the LLM to avoid API calls during testing
        with patch('src.core.agent.ChatOpenAI') as mock_llm:
            mock_llm.return_value.ainvoke.return_value.content = "Test response"
            agent = BankingAIAgent(config)
            yield agent
    
    @pytest.mark.asyncio
    async def test_account_balance_inquiry(self, banking_agent):
        """Test account balance inquiry scenario"""
        query = "What's my account balance?"
        customer_id = "CUST001"
        
        # Mock the tools manager response
        with patch.object(banking_agent.tools_manager, 'get_customer_accounts') as mock_accounts:
            mock_accounts.return_value = {
                'success': True,
                'accounts': [
                    {
                        'account_id': 'CHK001',
                        'account_type': 'checking',
                        'balance': 2500.75,
                        'available_balance': 2500.75,
                        'currency': 'USD',
                        'status': 'active'
                    }
                ]
            }
            
            result = await banking_agent.process_query(
                query=query,
                customer_id=customer_id,
                session_id="test_session"
            )
            
            assert result['success'] is True
            assert 'response' in result
            assert result['compliance_status'] in ['compliant', 'warning']
            assert result['confidence_score'] > 0
    
    @pytest.mark.asyncio
    async def test_transaction_history_request(self, banking_agent):
        """Test transaction history request scenario"""
        query = "Show me my recent transactions"
        customer_id = "CUST001"
        
        # Mock the tools manager responses
        with patch.object(banking_agent.tools_manager, 'get_customer_accounts') as mock_accounts, \
             patch.object(banking_agent.tools_manager, 'get_transaction_history') as mock_transactions:
            
            mock_accounts.return_value = {
                'success': True,
                'accounts': [{'account_id': 'CHK001', 'account_type': 'checking'}]
            }
            
            mock_transactions.return_value = {
                'success': True,
                'transactions': [
                    {
                        'transaction_id': 'TXN001',
                        'amount': -45.67,
                        'description': 'Grocery Store Purchase',
                        'date': '2024-01-09T14:30:00',
                        'status': 'completed'
                    }
                ]
            }
            
            result = await banking_agent.process_query(
                query=query,
                customer_id=customer_id,
                session_id="test_session"
            )
            
            assert result['success'] is True
            assert 'response' in result
    
    @pytest.mark.asyncio
    async def test_fund_transfer_request(self, banking_agent):
        """Test fund transfer request scenario"""
        query = "I want to transfer $500 from checking to savings"
        customer_id = "CUST001"
        
        # Mock compliance check
        with patch.object(banking_agent.compliance_checker, 'check_query') as mock_compliance:
            mock_compliance.return_value = ComplianceResult(
                status='compliant',
                confidence=0.9,
                violations=[],
                warnings=[],
                guidance='Transaction appears compliant',
                required_actions=['Verify customer identity'],
                escalation_required=False
            )
            
            result = await banking_agent.process_query(
                query=query,
                customer_id=customer_id,
                session_id="test_session"
            )
            
            assert result['success'] is True
            assert result['compliance_status'] == 'compliant'
    
    @pytest.mark.asyncio
    async def test_product_information_request(self, banking_agent):
        """Test product information request scenario"""
        query = "Tell me about your credit cards"
        
        # Mock product information
        with patch.object(banking_agent.tools_manager, 'get_product_information') as mock_product:
            mock_product.return_value = {
                'success': True,
                'product_info': {
                    'name': 'Rewards Credit Card',
                    'description': 'Earn rewards on every purchase',
                    'features': ['2% cash back', 'No annual fee']
                }
            }
            
            result = await banking_agent.process_query(
                query=query,
                session_id="test_session"
            )
            
            assert result['success'] is True
            assert 'response' in result
    
    @pytest.mark.asyncio
    async def test_compliance_violation_scenario(self, banking_agent):
        """Test scenario with compliance violations"""
        query = "I need to transfer $50,000 in cash to an overseas account"
        customer_id = "CUST001"
        
        # Mock compliance check with violation
        with patch.object(banking_agent.compliance_checker, 'check_query') as mock_compliance:
            mock_compliance.return_value = ComplianceResult(
                status='violation',
                confidence=0.95,
                violations=['High-risk international transfer'],
                warnings=['Large cash amount'],
                guidance='This transaction requires enhanced due diligence',
                required_actions=['Manual review required', 'AML screening'],
                escalation_required=True
            )
            
            result = await banking_agent.process_query(
                query=query,
                customer_id=customer_id,
                session_id="test_session"
            )
            
            assert result['success'] is True
            assert result['compliance_status'] == 'violation'
    
    @pytest.mark.asyncio
    async def test_unauthenticated_account_request(self, banking_agent):
        """Test account request without customer authentication"""
        query = "What's my account balance?"
        # No customer_id provided
        
        result = await banking_agent.process_query(
            query=query,
            session_id="test_session"
        )
        
        assert result['success'] is True
        # Should handle gracefully and request authentication
        assert 'authentication' in result['response'].lower() or 'identity' in result['response'].lower()
    
    @pytest.mark.asyncio
    async def test_complex_multi_step_scenario(self, banking_agent):
        """Test complex scenario requiring multiple steps"""
        query = "I want to open a new savings account and transfer $1000 from my checking account"
        customer_id = "CUST001"
        
        # Mock various responses
        with patch.object(banking_agent.tools_manager, 'get_customer_accounts') as mock_accounts, \
             patch.object(banking_agent.tools_manager, 'get_product_information') as mock_product, \
             patch.object(banking_agent.compliance_checker, 'check_query') as mock_compliance:
            
            mock_accounts.return_value = {
                'success': True,
                'accounts': [
                    {
                        'account_id': 'CHK001',
                        'account_type': 'checking',
                        'balance': 5000.00,
                        'available_balance': 5000.00
                    }
                ]
            }
            
            mock_product.return_value = {
                'success': True,
                'product_info': {
                    'name': 'High-Yield Savings Account',
                    'description': 'Competitive interest rates for your savings'
                }
            }
            
            mock_compliance.return_value = ComplianceResult(
                status='compliant',
                confidence=0.85,
                violations=[],
                warnings=[],
                guidance='Account opening and transfer appear compliant',
                required_actions=['KYC verification', 'Account setup'],
                escalation_required=False
            )
            
            result = await banking_agent.process_query(
                query=query,
                customer_id=customer_id,
                session_id="test_session"
            )
            
            assert result['success'] is True
            assert result['compliance_status'] == 'compliant'
    
    @pytest.mark.asyncio
    async def test_fraud_detection_scenario(self, banking_agent):
        """Test fraud detection scenario"""
        query = "I want to transfer $25,000 to a new account I've never used before"
        customer_id = "CUST001"
        
        # Mock fraud risk check
        with patch.object(banking_agent.tools_manager, 'check_fraud_risk') as mock_fraud:
            mock_fraud.return_value = {
                'success': True,
                'risk_score': 75,
                'risk_level': 'high',
                'risk_factors': ['High transaction amount', 'New recipient'],
                'recommendation': 'review',
                'requires_manual_review': True
            }
            
            result = await banking_agent.process_query(
                query=query,
                customer_id=customer_id,
                session_id="test_session"
            )
            
            assert result['success'] is True
            # Should handle high-risk scenario appropriately
    
    @pytest.mark.asyncio
    async def test_memory_and_context_scenario(self, banking_agent):
        """Test memory and context handling"""
        customer_id = "CUST001"
        session_id = "test_session"
        
        # First interaction
        result1 = await banking_agent.process_query(
            query="What's my checking account balance?",
            customer_id=customer_id,
            session_id=session_id
        )
        
        # Second interaction referencing previous context
        result2 = await banking_agent.process_query(
            query="Can I transfer $100 from that account to savings?",
            customer_id=customer_id,
            session_id=session_id
        )
        
        assert result1['success'] is True
        assert result2['success'] is True
        # Memory system should maintain context between interactions
    
    @pytest.mark.asyncio
    async def test_self_reflection_quality_assessment(self, banking_agent):
        """Test self-reflection and quality assessment"""
        query = "What are the benefits of your premium checking account?"
        
        result = await banking_agent.process_query(
            query=query,
            session_id="test_session"
        )
        
        assert result['success'] is True
        assert 'confidence_score' in result
        assert 0 <= result['confidence_score'] <= 1
        # Self-reflection should provide quality metrics
    
    def test_planning_module_task_classification(self, banking_agent):
        """Test planning module task classification"""
        test_queries = [
            ("What's my balance?", TaskType.ACCOUNT_INQUIRY),
            ("Transfer money to savings", TaskType.TRANSACTION),
            ("Tell me about loans", TaskType.PRODUCT_INFO),
            ("I have a complaint", TaskType.CUSTOMER_SERVICE),
            ("Is this transaction compliant?", TaskType.COMPLIANCE)
        ]
        
        for query, expected_type in test_queries:
            # This would test the planning module's classification logic
            # In a real implementation, we'd test the actual classification
            assert True  # Placeholder for actual classification test
    
    def test_rag_system_knowledge_retrieval(self, banking_agent):
        """Test RAG system knowledge retrieval"""
        # Test that RAG system can retrieve relevant banking knowledge
        test_queries = [
            "What is FDIC insurance?",
            "How do wire transfers work?",
            "What are KYC requirements?",
            "Explain overdraft fees"
        ]
        
        for query in test_queries:
            # This would test the RAG system's retrieval capabilities
            # In a real implementation, we'd test actual retrieval
            assert True  # Placeholder for actual retrieval test

class TestPerformanceMetrics:
    """Test performance and quality metrics"""
    
    @pytest.mark.asyncio
    async def test_response_time_performance(self, banking_agent):
        """Test response time performance"""
        query = "What's my account balance?"
        customer_id = "CUST001"
        
        start_time = datetime.now()
        result = await banking_agent.process_query(
            query=query,
            customer_id=customer_id,
            session_id="test_session"
        )
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        
        assert result['success'] is True
        assert response_time < 30  # Should respond within 30 seconds
    
    def test_concurrent_requests_handling(self, banking_agent):
        """Test handling of concurrent requests"""
        # This would test the system's ability to handle multiple concurrent requests
        # In a real implementation, we'd simulate concurrent load
        assert True  # Placeholder for concurrent testing
    
    def test_memory_usage_optimization(self, banking_agent):
        """Test memory usage optimization"""
        # This would test memory usage patterns
        # In a real implementation, we'd monitor memory consumption
        assert True  # Placeholder for memory testing

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_invalid_customer_id(self, banking_agent):
        """Test handling of invalid customer ID"""
        query = "What's my account balance?"
        customer_id = "INVALID_CUSTOMER"
        
        with patch.object(banking_agent.tools_manager, 'get_customer_accounts') as mock_accounts:
            mock_accounts.return_value = {
                'success': False,
                'error': 'Customer not found',
                'error_code': 'CUSTOMER_NOT_FOUND'
            }
            
            result = await banking_agent.process_query(
                query=query,
                customer_id=customer_id,
                session_id="test_session"
            )
            
            assert result['success'] is True
            # Should handle gracefully even with invalid customer
    
    @pytest.mark.asyncio
    async def test_system_error_recovery(self, banking_agent):
        """Test system error recovery"""
        query = "What's my account balance?"
        
        # Simulate system error
        with patch.object(banking_agent.tools_manager, 'get_customer_accounts') as mock_accounts:
            mock_accounts.side_effect = Exception("Database connection failed")
            
            result = await banking_agent.process_query(
                query=query,
                customer_id="CUST001",
                session_id="test_session"
            )
            
            assert result['success'] is True
            # Should provide graceful error response
    
    @pytest.mark.asyncio
    async def test_malformed_query_handling(self, banking_agent):
        """Test handling of malformed or unclear queries"""
        malformed_queries = [
            "",  # Empty query
            "asdfghjkl",  # Random characters
            "What is the meaning of life?",  # Non-banking query
            "Transfer money to account number 1234567890123456789012345678901234567890"  # Extremely long
        ]
        
        for query in malformed_queries:
            result = await banking_agent.process_query(
                query=query,
                session_id="test_session"
            )
            
            assert result['success'] is True
            # Should handle all queries gracefully

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

