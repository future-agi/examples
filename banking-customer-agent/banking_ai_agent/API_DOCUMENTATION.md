# Banking AI Agent - API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URL and Versioning](#base-url-and-versioning)
4. [Request/Response Format](#requestresponse-format)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Core Endpoints](#core-endpoints)
8. [Banking Operations](#banking-operations)
9. [Compliance and Security](#compliance-and-security)
10. [Monitoring and Analytics](#monitoring-and-analytics)
11. [WebSocket API](#websocket-api)
12. [SDK and Examples](#sdk-and-examples)

## Overview

The Banking AI Agent API provides a comprehensive set of endpoints for integrating intelligent banking services into your applications. The API supports real-time customer interactions, account management, transaction processing, compliance checking, and advanced AI-powered banking operations.

### Key Features

- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Format**: All requests and responses use JSON
- **Real-time Processing**: Instant response capabilities
- **Compliance Built-in**: Automatic regulatory compliance checking
- **Secure by Default**: Enterprise-grade security features
- **Comprehensive Logging**: Full audit trail for all operations

### API Capabilities

- Customer conversation management
- Account balance and transaction inquiries
- Fund transfers and payment processing
- Product information and recommendations
- Compliance and fraud detection
- Real-time monitoring and analytics

## Authentication

### API Key Authentication

All API requests require authentication using an API key passed in the request header.

```http
X-API-Key: your-api-key-here
```

### JWT Token Authentication

For enhanced security, JWT tokens can be used for session-based authentication.

```http
Authorization: Bearer your-jwt-token-here
```

### Customer Authentication

Customer-specific operations require customer identification:

```json
{
  "customer_id": "CUST001",
  "session_id": "session_123456"
}
```

## Base URL and Versioning

**Base URL:** `https://api.banking-ai-agent.com`

**Current Version:** `v1`

**Full Base URL:** `https://api.banking-ai-agent.com/v1`

### Version Headers

```http
Accept: application/vnd.banking-ai-agent.v1+json
Content-Type: application/json
```

## Request/Response Format

### Standard Request Format

```json
{
  "query": "What's my account balance?",
  "customer_id": "CUST001",
  "session_id": "session_123456",
  "context": {
    "channel": "web",
    "device": "desktop",
    "location": "US"
  },
  "metadata": {
    "timestamp": "2024-01-10T15:30:00Z",
    "request_id": "req_123456"
  }
}
```

### Standard Response Format

```json
{
  "success": true,
  "response": "Your checking account balance is $2,500.75",
  "data": {
    "account_balance": 2500.75,
    "account_type": "checking",
    "currency": "USD"
  },
  "metadata": {
    "confidence_score": 0.95,
    "compliance_status": "compliant",
    "execution_time": 1.23,
    "plan_id": "plan_789",
    "timestamp": "2024-01-10T15:30:01Z",
    "request_id": "req_123456"
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_CUSTOMER_ID",
    "message": "The provided customer ID is invalid or not found",
    "details": {
      "customer_id": "INVALID_CUST",
      "suggestion": "Please verify the customer ID and try again"
    }
  },
  "metadata": {
    "timestamp": "2024-01-10T15:30:00Z",
    "request_id": "req_123456"
  }
}
```

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_API_KEY` | API key is missing or invalid |
| `INVALID_CUSTOMER_ID` | Customer ID is invalid or not found |
| `INSUFFICIENT_FUNDS` | Account has insufficient funds for transaction |
| `COMPLIANCE_VIOLATION` | Request violates compliance rules |
| `FRAUD_DETECTED` | Potential fraud detected |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

## Rate Limiting

### Rate Limits

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Chat/Conversation | 100 requests | 1 minute |
| Account Operations | 50 requests | 1 minute |
| Transaction Operations | 20 requests | 1 minute |
| Compliance Checks | 200 requests | 1 minute |
| Health/Status | 1000 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641825600
```

## Core Endpoints

### Health Check

Check the health and status of the Banking AI Agent service.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-10T15:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "response_time": 12
    },
    "openai": {
      "status": "healthy",
      "response_time": 245
    },
    "memory_system": {
      "status": "healthy",
      "active_sessions": 24
    },
    "rag_system": {
      "status": "healthy",
      "knowledge_base_size": 15000
    }
  }
}
```

### Chat Interface

Process customer queries and provide intelligent responses.

**Endpoint:** `POST /chat`

**Request:**
```json
{
  "query": "What's my account balance?",
  "customer_id": "CUST001",
  "session_id": "session_123456",
  "context": {
    "channel": "web",
    "previous_queries": ["Hello", "I need help with my account"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "response": "Your checking account (****1234) has a current balance of $2,500.75. Your savings account (****5678) has a balance of $15,750.00. Is there anything specific you'd like to know about your accounts?",
  "data": {
    "accounts": [
      {
        "account_id": "CHK001",
        "account_type": "checking",
        "masked_number": "****1234",
        "balance": 2500.75,
        "available_balance": 2500.75,
        "currency": "USD"
      },
      {
        "account_id": "SAV001",
        "account_type": "savings",
        "masked_number": "****5678",
        "balance": 15750.00,
        "available_balance": 15750.00,
        "currency": "USD"
      }
    ]
  },
  "metadata": {
    "confidence_score": 0.98,
    "compliance_status": "compliant",
    "execution_time": 1.45,
    "plan_id": "plan_balance_inquiry_001",
    "tools_used": ["account_lookup", "balance_retrieval"],
    "timestamp": "2024-01-10T15:30:01Z"
  }
}
```

### Conversation History

Retrieve conversation history for a customer session.

**Endpoint:** `GET /conversations/{customer_id}/{session_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": "CUST001",
    "session_id": "session_123456",
    "conversation_start": "2024-01-10T15:00:00Z",
    "messages": [
      {
        "id": "msg_001",
        "type": "customer",
        "content": "Hello, I need help with my account",
        "timestamp": "2024-01-10T15:00:00Z"
      },
      {
        "id": "msg_002",
        "type": "agent",
        "content": "Hello! I'm here to help you with your banking needs. How can I assist you today?",
        "timestamp": "2024-01-10T15:00:01Z",
        "confidence_score": 0.95,
        "compliance_status": "compliant"
      }
    ],
    "total_messages": 2,
    "session_status": "active"
  }
}
```

## Banking Operations

### Account Balance

Get account balance for a specific customer and account.

**Endpoint:** `POST /account/balance`

**Request:**
```json
{
  "customer_id": "CUST001",
  "account_id": "CHK001"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "account_id": "CHK001",
    "account_type": "checking",
    "account_number": "****1234",
    "balance": 2500.75,
    "available_balance": 2500.75,
    "pending_transactions": 0,
    "currency": "USD",
    "last_updated": "2024-01-10T15:30:00Z"
  }
}
```

### Transaction History

Retrieve transaction history for an account.

**Endpoint:** `POST /account/transactions`

**Request:**
```json
{
  "customer_id": "CUST001",
  "account_id": "CHK001",
  "limit": 10,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-10T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "account_id": "CHK001",
    "transactions": [
      {
        "transaction_id": "TXN001",
        "type": "debit",
        "amount": -45.67,
        "description": "Grocery Store Purchase",
        "merchant": "SuperMart",
        "category": "groceries",
        "date": "2024-01-09T14:30:00Z",
        "status": "completed",
        "balance_after": 2500.75
      },
      {
        "transaction_id": "TXN002",
        "type": "credit",
        "amount": 2000.00,
        "description": "Direct Deposit - Salary",
        "date": "2024-01-08T09:00:00Z",
        "status": "completed",
        "balance_after": 2546.42
      }
    ],
    "total_transactions": 2,
    "page": 1,
    "has_more": false
  }
}
```

### Fund Transfer

Transfer funds between accounts.

**Endpoint:** `POST /transfer`

**Request:**
```json
{
  "customer_id": "CUST001",
  "from_account": "CHK001",
  "to_account": "SAV001",
  "amount": 500.00,
  "description": "Transfer to savings",
  "scheduled_date": "2024-01-10T16:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transfer_id": "TRF001",
    "from_account": "CHK001",
    "to_account": "SAV001",
    "amount": 500.00,
    "description": "Transfer to savings",
    "status": "pending",
    "scheduled_date": "2024-01-10T16:00:00Z",
    "estimated_completion": "2024-01-10T16:00:30Z",
    "reference_number": "REF123456789"
  },
  "metadata": {
    "compliance_status": "compliant",
    "fraud_score": 0.05,
    "execution_time": 0.89
  }
}
```

### Account Information

Get comprehensive account information.

**Endpoint:** `GET /account/{customer_id}/{account_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "account_id": "CHK001",
    "account_type": "checking",
    "account_number": "****1234",
    "account_name": "Primary Checking",
    "balance": 2500.75,
    "available_balance": 2500.75,
    "currency": "USD",
    "status": "active",
    "opened_date": "2020-03-15T00:00:00Z",
    "interest_rate": 0.01,
    "minimum_balance": 100.00,
    "overdraft_protection": true,
    "features": [
      "online_banking",
      "mobile_deposits",
      "bill_pay",
      "overdraft_protection"
    ],
    "restrictions": [],
    "last_statement_date": "2024-01-01T00:00:00Z",
    "next_statement_date": "2024-02-01T00:00:00Z"
  }
}
```

## Product Information

### Get Product Details

Retrieve information about banking products.

**Endpoint:** `GET /products/{product_type}`

**Parameters:**
- `product_type`: credit_cards, loans, savings, checking, investments

**Response:**
```json
{
  "success": true,
  "data": {
    "product_type": "credit_cards",
    "products": [
      {
        "product_id": "CC001",
        "name": "Rewards Credit Card",
        "description": "Earn 2% cash back on all purchases with no annual fee",
        "features": [
          "2% cash back on all purchases",
          "No annual fee",
          "0% intro APR for 12 months",
          "Fraud protection",
          "Mobile app access"
        ],
        "apr": {
          "purchase": "15.99% - 25.99%",
          "balance_transfer": "15.99% - 25.99%",
          "cash_advance": "29.99%"
        },
        "fees": {
          "annual_fee": 0,
          "balance_transfer_fee": "3% or $5 minimum",
          "cash_advance_fee": "5% or $10 minimum",
          "foreign_transaction_fee": 0
        },
        "eligibility": {
          "minimum_credit_score": 650,
          "minimum_income": 25000,
          "employment_required": true
        },
        "application_url": "https://apply.bank.com/credit-cards/rewards"
      }
    ]
  }
}
```

## Compliance and Security

### Compliance Check

Check if a query or operation complies with banking regulations.

**Endpoint:** `POST /compliance/check`

**Request:**
```json
{
  "query": "I want to transfer $50,000 to an overseas account",
  "customer_id": "CUST001",
  "context": {
    "transaction_type": "international_wire",
    "amount": 50000,
    "destination_country": "Switzerland"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "compliance_result": {
      "status": "warning",
      "confidence": 0.85,
      "violations": [],
      "warnings": [
        "Large international transfer requires enhanced due diligence",
        "Transaction amount exceeds daily limit"
      ],
      "guidance": "This transaction requires additional verification and may be subject to regulatory reporting requirements under the Bank Secrecy Act.",
      "required_actions": [
        "Customer identity verification",
        "Source of funds documentation",
        "Purpose of transfer documentation",
        "Beneficiary verification"
      ],
      "escalation_required": true,
      "estimated_processing_time": "2-5 business days"
    },
    "regulatory_requirements": [
      {
        "regulation": "BSA",
        "requirement": "CTR filing required for transactions over $10,000",
        "applicable": true
      },
      {
        "regulation": "AML",
        "requirement": "Enhanced due diligence for high-risk countries",
        "applicable": true
      }
    ]
  }
}
```

### Fraud Detection

Check for potential fraud in transactions or activities.

**Endpoint:** `POST /fraud/check`

**Request:**
```json
{
  "customer_id": "CUST001",
  "transaction_type": "transfer",
  "amount": 25000,
  "destination": "new_account",
  "context": {
    "time_of_day": "03:00",
    "location": "unusual",
    "device": "new"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "fraud_assessment": {
      "risk_score": 75,
      "risk_level": "high",
      "recommendation": "review",
      "confidence": 0.88,
      "risk_factors": [
        "High transaction amount",
        "New recipient account",
        "Unusual time of transaction",
        "New device used",
        "Geographic anomaly"
      ],
      "protective_actions": [
        "Transaction hold",
        "Customer verification required",
        "Manual review initiated"
      ],
      "requires_manual_review": true,
      "estimated_review_time": "2-4 hours"
    },
    "historical_patterns": {
      "average_transaction_amount": 500,
      "typical_transaction_times": ["09:00-17:00"],
      "usual_recipients": ["SAV001", "CHK002"],
      "device_history": ["iPhone_12", "Chrome_Desktop"]
    }
  }
}
```

## Monitoring and Analytics

### Quality Metrics

Get AI quality and performance metrics.

**Endpoint:** `GET /analytics/quality`

**Response:**
```json
{
  "success": true,
  "data": {
    "quality_metrics": {
      "average_confidence": 0.92,
      "average_accuracy": 0.89,
      "average_completeness": 0.94,
      "average_clarity": 0.91,
      "total_interactions": 15847,
      "successful_resolutions": 14256,
      "escalation_rate": 0.08,
      "customer_satisfaction": 4.6,
      "recent_trend": "improving"
    },
    "performance_metrics": {
      "average_response_time": 1.23,
      "p95_response_time": 2.45,
      "p99_response_time": 4.12,
      "uptime_percentage": 99.97,
      "error_rate": 0.003
    },
    "compliance_metrics": {
      "compliance_rate": 0.962,
      "violations_detected": 12,
      "warnings_issued": 89,
      "escalations_required": 23
    }
  }
}
```

### System Status

Get detailed system status and component health.

**Endpoint:** `GET /status`

**Response:**
```json
{
  "success": true,
  "data": {
    "system_status": {
      "overall_status": "healthy",
      "uptime": "15d 7h 23m",
      "version": "1.0.0",
      "environment": "production"
    },
    "components": {
      "planning_module": {
        "status": "healthy",
        "response_time": 45,
        "active_plans": 12,
        "completed_plans": 1547
      },
      "rag_system": {
        "status": "healthy",
        "response_time": 89,
        "knowledge_base_size": 15000,
        "index_health": "optimal"
      },
      "memory_system": {
        "status": "healthy",
        "active_sessions": 24,
        "memory_usage": "68%",
        "cache_hit_rate": 0.94
      },
      "compliance_checker": {
        "status": "healthy",
        "rules_loaded": 156,
        "last_update": "2024-01-10T12:00:00Z"
      }
    },
    "resource_usage": {
      "cpu_usage": 45.2,
      "memory_usage": 68.7,
      "disk_usage": 23.1,
      "network_io": "normal"
    }
  }
}
```

## WebSocket API

### Real-time Chat

Establish a WebSocket connection for real-time chat interactions.

**WebSocket URL:** `wss://api.banking-ai-agent.com/v1/ws/chat`

**Connection Parameters:**
```javascript
const ws = new WebSocket('wss://api.banking-ai-agent.com/v1/ws/chat', {
  headers: {
    'X-API-Key': 'your-api-key',
    'Customer-ID': 'CUST001',
    'Session-ID': 'session_123456'
  }
});
```

**Message Format:**
```json
{
  "type": "message",
  "data": {
    "query": "What's my account balance?",
    "timestamp": "2024-01-10T15:30:00Z"
  }
}
```

**Response Format:**
```json
{
  "type": "response",
  "data": {
    "response": "Your checking account balance is $2,500.75",
    "confidence_score": 0.95,
    "compliance_status": "compliant",
    "timestamp": "2024-01-10T15:30:01Z"
  }
}
```

### Real-time Notifications

Subscribe to real-time notifications for account activities.

**WebSocket URL:** `wss://api.banking-ai-agent.com/v1/ws/notifications`

**Subscription Message:**
```json
{
  "type": "subscribe",
  "data": {
    "customer_id": "CUST001",
    "notification_types": ["transactions", "alerts", "compliance"]
  }
}
```

**Notification Format:**
```json
{
  "type": "notification",
  "data": {
    "notification_type": "transaction",
    "title": "New Transaction",
    "message": "A debit of $45.67 was processed on your checking account",
    "transaction_id": "TXN001",
    "timestamp": "2024-01-10T15:30:00Z"
  }
}
```

## SDK and Examples

### JavaScript SDK

```javascript
// Install: npm install banking-ai-agent-sdk

import BankingAIAgent from 'banking-ai-agent-sdk';

const client = new BankingAIAgent({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.banking-ai-agent.com/v1'
});

// Chat interaction
const response = await client.chat({
  query: "What's my account balance?",
  customerId: "CUST001",
  sessionId: "session_123456"
});

console.log(response.data.response);

// Account balance
const balance = await client.getAccountBalance({
  customerId: "CUST001",
  accountId: "CHK001"
});

console.log(`Balance: $${balance.data.balance}`);

// Fund transfer
const transfer = await client.transferFunds({
  customerId: "CUST001",
  fromAccount: "CHK001",
  toAccount: "SAV001",
  amount: 500.00,
  description: "Transfer to savings"
});

console.log(`Transfer ID: ${transfer.data.transfer_id}`);
```

### Python SDK

```python
# Install: pip install banking-ai-agent-sdk

from banking_ai_agent_sdk import BankingAIAgent

client = BankingAIAgent(
    api_key="your-api-key",
    base_url="https://api.banking-ai-agent.com/v1"
)

# Chat interaction
response = client.chat(
    query="What's my account balance?",
    customer_id="CUST001",
    session_id="session_123456"
)

print(response.data.response)

# Account balance
balance = client.get_account_balance(
    customer_id="CUST001",
    account_id="CHK001"
)

print(f"Balance: ${balance.data.balance}")

# Fund transfer
transfer = client.transfer_funds(
    customer_id="CUST001",
    from_account="CHK001",
    to_account="SAV001",
    amount=500.00,
    description="Transfer to savings"
)

print(f"Transfer ID: {transfer.data.transfer_id}")
```

### cURL Examples

**Chat Request:**
```bash
curl -X POST https://api.banking-ai-agent.com/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "What'\''s my account balance?",
    "customer_id": "CUST001",
    "session_id": "session_123456"
  }'
```

**Account Balance:**
```bash
curl -X POST https://api.banking-ai-agent.com/v1/account/balance \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "CUST001",
    "account_id": "CHK001"
  }'
```

**Fund Transfer:**
```bash
curl -X POST https://api.banking-ai-agent.com/v1/transfer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "customer_id": "CUST001",
    "from_account": "CHK001",
    "to_account": "SAV001",
    "amount": 500.00,
    "description": "Transfer to savings"
  }'
```

This comprehensive API documentation provides all the necessary information for integrating with the Banking AI Agent, including detailed examples, error handling, and best practices for secure banking operations.

