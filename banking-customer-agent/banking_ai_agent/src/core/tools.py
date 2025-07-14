"""
Banking Tools Manager - System Integrations and Operations
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import random

@dataclass
class AccountInfo:
    """Account information structure"""
    account_id: str
    account_type: str
    balance: float
    available_balance: float
    currency: str
    status: str
    last_transaction_date: str

@dataclass
class Transaction:
    """Transaction information structure"""
    transaction_id: str
    account_id: str
    amount: float
    transaction_type: str
    description: str
    date: str
    status: str
    reference_number: str

@dataclass
class TransferResult:
    """Transfer operation result"""
    transfer_id: str
    status: str
    amount: float
    from_account: str
    to_account: str
    confirmation_number: str
    estimated_completion: str

class BankingToolsManager:
    """
    Banking tools manager for system integrations and operations
    Note: This is a simulation layer - in production, these would integrate with actual banking systems
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('BankingToolsManager')
        
        # Simulated data stores (in production, these would be actual system integrations)
        self.accounts_db = {}
        self.transactions_db = {}
        self.customers_db = {}
        
        # Initialize with sample data
        self._init_sample_data()
        
    def _init_sample_data(self):
        """Initialize with sample banking data for demonstration"""
        # Sample customer accounts
        sample_accounts = [
            {
                'customer_id': 'CUST001',
                'accounts': [
                    AccountInfo(
                        account_id='CHK001',
                        account_type='checking',
                        balance=2500.75,
                        available_balance=2500.75,
                        currency='USD',
                        status='active',
                        last_transaction_date='2024-01-09'
                    ),
                    AccountInfo(
                        account_id='SAV001',
                        account_type='savings',
                        balance=15000.00,
                        available_balance=15000.00,
                        currency='USD',
                        status='active',
                        last_transaction_date='2024-01-08'
                    )
                ]
            },
            {
                'customer_id': 'CUST002',
                'accounts': [
                    AccountInfo(
                        account_id='CHK002',
                        account_type='checking',
                        balance=1250.30,
                        available_balance=1250.30,
                        currency='USD',
                        status='active',
                        last_transaction_date='2024-01-10'
                    )
                ]
            }
        ]
        
        # Store sample accounts
        for customer_data in sample_accounts:
            self.accounts_db[customer_data['customer_id']] = customer_data['accounts']
        
        # Sample transactions
        sample_transactions = [
            Transaction(
                transaction_id='TXN001',
                account_id='CHK001',
                amount=-45.67,
                transaction_type='debit',
                description='Grocery Store Purchase',
                date='2024-01-09T14:30:00',
                status='completed',
                reference_number='REF001'
            ),
            Transaction(
                transaction_id='TXN002',
                account_id='CHK001',
                amount=1200.00,
                transaction_type='credit',
                description='Direct Deposit - Salary',
                date='2024-01-08T09:00:00',
                status='completed',
                reference_number='REF002'
            ),
            Transaction(
                transaction_id='TXN003',
                account_id='SAV001',
                amount=500.00,
                transaction_type='credit',
                description='Transfer from Checking',
                date='2024-01-08T15:45:00',
                status='completed',
                reference_number='REF003'
            )
        ]
        
        # Store sample transactions
        for transaction in sample_transactions:
            if transaction.account_id not in self.transactions_db:
                self.transactions_db[transaction.account_id] = []
            self.transactions_db[transaction.account_id].append(transaction)
    
    async def get_account_balance(self, customer_id: str, account_id: str) -> Dict[str, Any]:
        """Get account balance information"""
        try:
            self.logger.info(f"Getting balance for account {account_id}")
            
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            # Find customer accounts
            if customer_id not in self.accounts_db:
                return {
                    'success': False,
                    'error': 'Customer not found',
                    'error_code': 'CUSTOMER_NOT_FOUND'
                }
            
            # Find specific account
            account = None
            for acc in self.accounts_db[customer_id]:
                if acc.account_id == account_id:
                    account = acc
                    break
            
            if not account:
                return {
                    'success': False,
                    'error': 'Account not found',
                    'error_code': 'ACCOUNT_NOT_FOUND'
                }
            
            return {
                'success': True,
                'account_id': account.account_id,
                'account_type': account.account_type,
                'balance': account.balance,
                'available_balance': account.available_balance,
                'currency': account.currency,
                'status': account.status,
                'last_transaction_date': account.last_transaction_date,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account balance: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYSTEM_ERROR'
            }
    
    async def get_transaction_history(self, 
                                    customer_id: str, 
                                    account_id: str, 
                                    limit: int = 10,
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get transaction history for an account"""
        try:
            self.logger.info(f"Getting transaction history for account {account_id}")
            
            # Simulate API delay
            await asyncio.sleep(0.2)
            
            # Verify customer and account
            balance_check = await self.get_account_balance(customer_id, account_id)
            if not balance_check['success']:
                return balance_check
            
            # Get transactions for account
            transactions = self.transactions_db.get(account_id, [])
            
            # Filter by date range if provided
            filtered_transactions = []
            for txn in transactions:
                txn_date = datetime.fromisoformat(txn.date.replace('Z', '+00:00'))
                
                include_txn = True
                if start_date:
                    start_dt = datetime.fromisoformat(start_date)
                    if txn_date < start_dt:
                        include_txn = False
                
                if end_date and include_txn:
                    end_dt = datetime.fromisoformat(end_date)
                    if txn_date > end_dt:
                        include_txn = False
                
                if include_txn:
                    filtered_transactions.append(txn)
            
            # Sort by date (most recent first) and limit
            filtered_transactions.sort(key=lambda x: x.date, reverse=True)
            limited_transactions = filtered_transactions[:limit]
            
            # Convert to dict format
            transaction_list = []
            for txn in limited_transactions:
                transaction_list.append({
                    'transaction_id': txn.transaction_id,
                    'amount': txn.amount,
                    'transaction_type': txn.transaction_type,
                    'description': txn.description,
                    'date': txn.date,
                    'status': txn.status,
                    'reference_number': txn.reference_number
                })
            
            return {
                'success': True,
                'account_id': account_id,
                'transactions': transaction_list,
                'total_count': len(filtered_transactions),
                'returned_count': len(transaction_list),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting transaction history: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYSTEM_ERROR'
            }
    
    async def transfer_funds(self,
                           customer_id: str,
                           from_account: str,
                           to_account: str,
                           amount: float,
                           description: str = "") -> Dict[str, Any]:
        """Transfer funds between accounts"""
        try:
            self.logger.info(f"Processing transfer: ${amount} from {from_account} to {to_account}")
            
            # Simulate processing delay
            await asyncio.sleep(0.5)
            
            # Validate amount
            if amount <= 0:
                return {
                    'success': False,
                    'error': 'Transfer amount must be positive',
                    'error_code': 'INVALID_AMOUNT'
                }
            
            # Check source account balance
            from_balance = await self.get_account_balance(customer_id, from_account)
            if not from_balance['success']:
                return from_balance
            
            if from_balance['available_balance'] < amount:
                return {
                    'success': False,
                    'error': 'Insufficient funds',
                    'error_code': 'INSUFFICIENT_FUNDS',
                    'available_balance': from_balance['available_balance'],
                    'requested_amount': amount
                }
            
            # Validate destination account (simplified - in production would check routing, etc.)
            if to_account.startswith('CHK') or to_account.startswith('SAV'):
                # Internal transfer
                to_balance = await self.get_account_balance(customer_id, to_account)
                if not to_balance['success']:
                    return {
                        'success': False,
                        'error': 'Destination account not found',
                        'error_code': 'DESTINATION_ACCOUNT_NOT_FOUND'
                    }
            
            # Generate transfer ID and confirmation
            transfer_id = f"TRF{random.randint(100000, 999999)}"
            confirmation_number = f"CONF{random.randint(1000000, 9999999)}"
            
            # Simulate transfer processing
            # In production, this would involve actual account debiting/crediting
            
            # Create debit transaction for source account
            debit_txn = Transaction(
                transaction_id=f"TXN{random.randint(10000, 99999)}",
                account_id=from_account,
                amount=-amount,
                transaction_type='debit',
                description=f"Transfer to {to_account}: {description}",
                date=datetime.now().isoformat(),
                status='completed',
                reference_number=confirmation_number
            )
            
            # Add to transactions
            if from_account not in self.transactions_db:
                self.transactions_db[from_account] = []
            self.transactions_db[from_account].append(debit_txn)
            
            # Update source account balance
            for account in self.accounts_db.get(customer_id, []):
                if account.account_id == from_account:
                    account.balance -= amount
                    account.available_balance -= amount
                    account.last_transaction_date = datetime.now().date().isoformat()
                    break
            
            # If internal transfer, create credit transaction
            if to_account.startswith('CHK') or to_account.startswith('SAV'):
                credit_txn = Transaction(
                    transaction_id=f"TXN{random.randint(10000, 99999)}",
                    account_id=to_account,
                    amount=amount,
                    transaction_type='credit',
                    description=f"Transfer from {from_account}: {description}",
                    date=datetime.now().isoformat(),
                    status='completed',
                    reference_number=confirmation_number
                )
                
                if to_account not in self.transactions_db:
                    self.transactions_db[to_account] = []
                self.transactions_db[to_account].append(credit_txn)
                
                # Update destination account balance
                for account in self.accounts_db.get(customer_id, []):
                    if account.account_id == to_account:
                        account.balance += amount
                        account.available_balance += amount
                        account.last_transaction_date = datetime.now().date().isoformat()
                        break
            
            # Determine completion time
            if to_account.startswith('CHK') or to_account.startswith('SAV'):
                completion_time = "Immediate"
            else:
                completion_time = "1-3 business days"
            
            return {
                'success': True,
                'transfer_id': transfer_id,
                'confirmation_number': confirmation_number,
                'amount': amount,
                'from_account': from_account,
                'to_account': to_account,
                'description': description,
                'status': 'completed' if completion_time == "Immediate" else 'processing',
                'estimated_completion': completion_time,
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing transfer: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYSTEM_ERROR'
            }
    
    async def get_customer_accounts(self, customer_id: str) -> Dict[str, Any]:
        """Get all accounts for a customer"""
        try:
            self.logger.info(f"Getting accounts for customer {customer_id}")
            
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            if customer_id not in self.accounts_db:
                return {
                    'success': False,
                    'error': 'Customer not found',
                    'error_code': 'CUSTOMER_NOT_FOUND'
                }
            
            accounts = []
            for account in self.accounts_db[customer_id]:
                accounts.append({
                    'account_id': account.account_id,
                    'account_type': account.account_type,
                    'balance': account.balance,
                    'available_balance': account.available_balance,
                    'currency': account.currency,
                    'status': account.status,
                    'last_transaction_date': account.last_transaction_date
                })
            
            return {
                'success': True,
                'customer_id': customer_id,
                'accounts': accounts,
                'account_count': len(accounts),
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting customer accounts: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYSTEM_ERROR'
            }
    
    async def validate_account(self, account_id: str, routing_number: Optional[str] = None) -> Dict[str, Any]:
        """Validate account information"""
        try:
            self.logger.info(f"Validating account {account_id}")
            
            # Simulate validation delay
            await asyncio.sleep(0.2)
            
            # Simple validation logic (in production, would use actual validation services)
            is_valid = False
            account_type = 'unknown'
            bank_name = 'Unknown Bank'
            
            # Check if it's one of our internal accounts
            for customer_accounts in self.accounts_db.values():
                for account in customer_accounts:
                    if account.account_id == account_id:
                        is_valid = True
                        account_type = account.account_type
                        bank_name = 'Your Bank'
                        break
                if is_valid:
                    break
            
            # If not internal, simulate external validation
            if not is_valid and len(account_id) >= 8:
                # Simulate external account validation
                is_valid = True
                account_type = 'checking'  # Default assumption
                bank_name = 'External Bank'
            
            return {
                'success': True,
                'account_id': account_id,
                'is_valid': is_valid,
                'account_type': account_type,
                'bank_name': bank_name,
                'routing_number': routing_number,
                'validated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error validating account: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYSTEM_ERROR'
            }
    
    async def check_fraud_risk(self, 
                             customer_id: str,
                             transaction_type: str,
                             amount: float,
                             account_id: str) -> Dict[str, Any]:
        """Check fraud risk for a transaction"""
        try:
            self.logger.info(f"Checking fraud risk for {transaction_type} of ${amount}")
            
            # Simulate fraud check delay
            await asyncio.sleep(0.3)
            
            risk_score = 0
            risk_factors = []
            
            # Amount-based risk assessment
            if amount > 10000:
                risk_score += 30
                risk_factors.append("High transaction amount")
            elif amount > 5000:
                risk_score += 15
                risk_factors.append("Elevated transaction amount")
            
            # Transaction type risk
            if transaction_type in ['wire_transfer', 'international_transfer']:
                risk_score += 20
                risk_factors.append("High-risk transaction type")
            
            # Frequency check (simplified)
            recent_transactions = await self.get_transaction_history(customer_id, account_id, limit=5)
            if recent_transactions['success']:
                recent_count = len(recent_transactions['transactions'])
                if recent_count >= 5:
                    risk_score += 10
                    risk_factors.append("High transaction frequency")
            
            # Time-based risk (simplified)
            current_hour = datetime.now().hour
            if current_hour < 6 or current_hour > 22:
                risk_score += 5
                risk_factors.append("Unusual transaction time")
            
            # Determine risk level
            if risk_score >= 50:
                risk_level = 'high'
                recommendation = 'block'
            elif risk_score >= 25:
                risk_level = 'medium'
                recommendation = 'review'
            else:
                risk_level = 'low'
                recommendation = 'approve'
            
            return {
                'success': True,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendation': recommendation,
                'requires_manual_review': risk_score >= 25,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking fraud risk: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYSTEM_ERROR'
            }
    
    async def get_product_information(self, product_type: str) -> Dict[str, Any]:
        """Get banking product information"""
        try:
            self.logger.info(f"Getting product information for {product_type}")
            
            # Simulate API delay
            await asyncio.sleep(0.1)
            
            # Product information database
            products = {
                'checking': {
                    'name': 'Premium Checking Account',
                    'description': 'Full-featured checking account with no monthly fees',
                    'features': [
                        'No monthly maintenance fee',
                        'Free online and mobile banking',
                        'Free debit card',
                        'Free ATM access at network ATMs',
                        'Mobile check deposit'
                    ],
                    'requirements': {
                        'minimum_opening_deposit': 25.00,
                        'minimum_balance': 0.00,
                        'age_requirement': 18
                    },
                    'fees': {
                        'overdraft_fee': 35.00,
                        'foreign_transaction_fee': '3% of transaction',
                        'wire_transfer_fee': 25.00
                    }
                },
                'savings': {
                    'name': 'High-Yield Savings Account',
                    'description': 'Competitive interest rates for your savings',
                    'features': [
                        'Competitive interest rates',
                        'FDIC insured up to $250,000',
                        'Online and mobile banking',
                        'No minimum balance requirement',
                        'Automatic savings programs'
                    ],
                    'requirements': {
                        'minimum_opening_deposit': 1.00,
                        'minimum_balance': 0.00,
                        'age_requirement': 18
                    },
                    'interest_rate': '4.50% APY',
                    'fees': {
                        'excessive_withdrawal_fee': 10.00
                    }
                },
                'credit_card': {
                    'name': 'Rewards Credit Card',
                    'description': 'Earn rewards on every purchase',
                    'features': [
                        '2% cash back on all purchases',
                        'No annual fee',
                        '0% intro APR for 12 months',
                        'Fraud protection',
                        'Mobile app management'
                    ],
                    'requirements': {
                        'minimum_credit_score': 650,
                        'minimum_income': 25000,
                        'age_requirement': 18
                    },
                    'terms': {
                        'apr_range': '15.99% - 25.99%',
                        'credit_limit': '$500 - $25,000',
                        'annual_fee': 0.00
                    }
                },
                'personal_loan': {
                    'name': 'Personal Loan',
                    'description': 'Fixed-rate personal loans for any purpose',
                    'features': [
                        'Fixed interest rates',
                        'No prepayment penalties',
                        'Fast approval process',
                        'Direct deposit available',
                        'Flexible terms'
                    ],
                    'requirements': {
                        'minimum_credit_score': 600,
                        'minimum_income': 30000,
                        'debt_to_income_ratio': 0.40
                    },
                    'terms': {
                        'loan_amount': '$1,000 - $50,000',
                        'apr_range': '6.99% - 24.99%',
                        'term_length': '2 - 7 years'
                    }
                }
            }
            
            if product_type.lower() not in products:
                return {
                    'success': False,
                    'error': 'Product type not found',
                    'error_code': 'PRODUCT_NOT_FOUND',
                    'available_products': list(products.keys())
                }
            
            product_info = products[product_type.lower()]
            
            return {
                'success': True,
                'product_type': product_type,
                'product_info': product_info,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting product information: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYSTEM_ERROR'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get banking tools manager status"""
        try:
            # Count total accounts and transactions
            total_accounts = sum(len(accounts) for accounts in self.accounts_db.values())
            total_transactions = sum(len(txns) for txns in self.transactions_db.values())
            
            return {
                "module": "tools",
                "status": "healthy",
                "statistics": {
                    "total_customers": len(self.accounts_db),
                    "total_accounts": total_accounts,
                    "total_transactions": total_transactions
                },
                "capabilities": [
                    "account_management",
                    "transaction_processing",
                    "fund_transfers",
                    "fraud_detection",
                    "product_information",
                    "account_validation"
                ],
                "available_tools": [
                    "get_account_balance",
                    "get_transaction_history",
                    "transfer_funds",
                    "get_customer_accounts",
                    "validate_account",
                    "check_fraud_risk",
                    "get_product_information"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tools status: {str(e)}")
            return {
                "module": "tools",
                "status": "error",
                "error": str(e)
            }

