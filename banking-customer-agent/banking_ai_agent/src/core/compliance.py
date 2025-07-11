"""
Compliance Checker - Regulatory and Security Compliance
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ComplianceResult:
    """Result of compliance check"""
    status: str  # 'compliant', 'warning', 'violation', 'requires_review'
    confidence: float
    violations: List[str]
    warnings: List[str]
    guidance: str
    required_actions: List[str]
    escalation_required: bool

class ComplianceChecker:
    """
    Advanced compliance checker for banking regulations and security
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('ComplianceChecker')
        
        # Compliance rules and patterns
        self._init_compliance_rules()
        
        # Sensitive data patterns
        self._init_sensitive_patterns()
        
    def _init_compliance_rules(self):
        """Initialize compliance rules and regulations"""
        self.compliance_rules = {
            'kyc_requirements': {
                'description': 'Know Your Customer verification requirements',
                'triggers': ['account opening', 'identity verification', 'customer onboarding'],
                'required_actions': [
                    'Verify customer identity with government-issued ID',
                    'Confirm customer address',
                    'Assess customer risk profile',
                    'Document verification process'
                ]
            },
            'aml_monitoring': {
                'description': 'Anti-Money Laundering monitoring and reporting',
                'triggers': ['large transactions', 'suspicious activity', 'unusual patterns'],
                'required_actions': [
                    'Monitor transaction patterns',
                    'Report suspicious activities',
                    'Maintain transaction records',
                    'Conduct enhanced due diligence if required'
                ]
            },
            'bsa_reporting': {
                'description': 'Bank Secrecy Act reporting requirements',
                'triggers': ['cash transactions over $10,000', 'suspicious activities'],
                'required_actions': [
                    'File Currency Transaction Reports (CTR)',
                    'File Suspicious Activity Reports (SAR)',
                    'Maintain required records',
                    'Report within specified timeframes'
                ]
            },
            'privacy_protection': {
                'description': 'Customer privacy and data protection',
                'triggers': ['personal information', 'account details', 'financial data'],
                'required_actions': [
                    'Protect customer personal information',
                    'Limit data sharing to authorized purposes',
                    'Obtain consent for data usage',
                    'Provide privacy disclosures'
                ]
            },
            'fair_lending': {
                'description': 'Fair lending and non-discrimination requirements',
                'triggers': ['loan applications', 'credit decisions', 'pricing'],
                'required_actions': [
                    'Ensure non-discriminatory practices',
                    'Document credit decisions',
                    'Provide adverse action notices',
                    'Monitor for disparate impact'
                ]
            }
        }
    
    def _init_sensitive_patterns(self):
        """Initialize patterns for detecting sensitive information"""
        self.sensitive_patterns = {
            'ssn': {
                'pattern': r'\b\d{3}-?\d{2}-?\d{4}\b',
                'description': 'Social Security Number',
                'risk_level': 'high'
            },
            'account_number': {
                'pattern': r'\b\d{8,17}\b',
                'description': 'Bank Account Number',
                'risk_level': 'high'
            },
            'credit_card': {
                'pattern': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                'description': 'Credit Card Number',
                'risk_level': 'high'
            },
            'routing_number': {
                'pattern': r'\b\d{9}\b',
                'description': 'Bank Routing Number',
                'risk_level': 'medium'
            },
            'phone_number': {
                'pattern': r'\b\d{3}-?\d{3}-?\d{4}\b',
                'description': 'Phone Number',
                'risk_level': 'low'
            },
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'description': 'Email Address',
                'risk_level': 'low'
            }
        }
    
    async def check_query(self, 
                         query: str, 
                         customer_id: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None) -> ComplianceResult:
        """
        Perform comprehensive compliance check on customer query
        """
        try:
            self.logger.info("Performing compliance check on query")
            
            violations = []
            warnings = []
            required_actions = []
            escalation_required = False
            
            # Check for sensitive data exposure
            sensitive_check = self._check_sensitive_data(query)
            if sensitive_check['violations']:
                violations.extend(sensitive_check['violations'])
            if sensitive_check['warnings']:
                warnings.extend(sensitive_check['warnings'])
            
            # Check regulatory compliance requirements
            regulatory_check = self._check_regulatory_compliance(query, context)
            if regulatory_check['required_actions']:
                required_actions.extend(regulatory_check['required_actions'])
            if regulatory_check['escalation_required']:
                escalation_required = True
            
            # Check customer authentication requirements
            auth_check = self._check_authentication_requirements(query, customer_id)
            if auth_check['violations']:
                violations.extend(auth_check['violations'])
            if auth_check['required_actions']:
                required_actions.extend(auth_check['required_actions'])
            
            # Check transaction compliance
            transaction_check = self._check_transaction_compliance(query)
            if transaction_check['warnings']:
                warnings.extend(transaction_check['warnings'])
            if transaction_check['required_actions']:
                required_actions.extend(transaction_check['required_actions'])
            
            # Determine overall compliance status
            if violations:
                status = 'violation'
                confidence = 0.9
            elif warnings or required_actions:
                status = 'warning'
                confidence = 0.7
            elif escalation_required:
                status = 'requires_review'
                confidence = 0.8
            else:
                status = 'compliant'
                confidence = 0.95
            
            # Generate guidance
            guidance = self._generate_compliance_guidance(
                violations, warnings, required_actions, escalation_required
            )
            
            return ComplianceResult(
                status=status,
                confidence=confidence,
                violations=violations,
                warnings=warnings,
                guidance=guidance,
                required_actions=list(set(required_actions)),  # Remove duplicates
                escalation_required=escalation_required
            )
            
        except Exception as e:
            self.logger.error(f"Error in compliance check: {str(e)}")
            return ComplianceResult(
                status='error',
                confidence=0.0,
                violations=[f"Compliance check failed: {str(e)}"],
                warnings=[],
                guidance="Unable to perform compliance check. Manual review required.",
                required_actions=["Manual compliance review"],
                escalation_required=True
            )
    
    def _check_sensitive_data(self, query: str) -> Dict[str, List[str]]:
        """Check for sensitive data in query"""
        violations = []
        warnings = []
        
        query_lower = query.lower()
        
        # Check for direct sensitive data patterns
        for pattern_name, pattern_info in self.sensitive_patterns.items():
            matches = re.findall(pattern_info['pattern'], query, re.IGNORECASE)
            if matches:
                if pattern_info['risk_level'] == 'high':
                    violations.append(f"Potential {pattern_info['description']} detected in query")
                else:
                    warnings.append(f"Possible {pattern_info['description']} detected in query")
        
        # Check for requests for sensitive information
        sensitive_requests = [
            'social security', 'ssn', 'account number', 'routing number',
            'credit card', 'pin', 'password', 'security code'
        ]
        
        for sensitive_term in sensitive_requests:
            if sensitive_term in query_lower:
                warnings.append(f"Query requests sensitive information: {sensitive_term}")
        
        return {
            'violations': violations,
            'warnings': warnings
        }
    
    def _check_regulatory_compliance(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check regulatory compliance requirements"""
        required_actions = []
        escalation_required = False
        
        query_lower = query.lower()
        
        # Check for KYC triggers
        kyc_triggers = ['open account', 'new account', 'identity', 'verification']
        if any(trigger in query_lower for trigger in kyc_triggers):
            required_actions.extend(self.compliance_rules['kyc_requirements']['required_actions'])
        
        # Check for AML triggers
        aml_triggers = ['large transfer', 'wire transfer', 'cash deposit', 'suspicious']
        if any(trigger in query_lower for trigger in aml_triggers):
            required_actions.extend(self.compliance_rules['aml_monitoring']['required_actions'])
        
        # Check for BSA reporting triggers
        bsa_triggers = ['$10,000', 'cash transaction', 'currency report']
        if any(trigger in query_lower for trigger in bsa_triggers):
            required_actions.extend(self.compliance_rules['bsa_reporting']['required_actions'])
            escalation_required = True
        
        # Check for fair lending triggers
        lending_triggers = ['loan', 'credit', 'mortgage', 'financing']
        if any(trigger in query_lower for trigger in lending_triggers):
            required_actions.extend(self.compliance_rules['fair_lending']['required_actions'])
        
        # Check for complex regulatory scenarios
        complex_scenarios = [
            'international transfer', 'foreign account', 'sanctions', 'embargo',
            'politically exposed person', 'pep', 'high risk customer'
        ]
        if any(scenario in query_lower for scenario in complex_scenarios):
            escalation_required = True
            required_actions.append("Enhanced due diligence required")
        
        return {
            'required_actions': required_actions,
            'escalation_required': escalation_required
        }
    
    def _check_authentication_requirements(self, query: str, customer_id: Optional[str]) -> Dict[str, List[str]]:
        """Check customer authentication requirements"""
        violations = []
        required_actions = []
        
        query_lower = query.lower()
        
        # Check for account-specific requests without customer ID
        account_requests = [
            'balance', 'transaction', 'statement', 'transfer', 'payment',
            'account information', 'personal information'
        ]
        
        if any(request in query_lower for request in account_requests):
            if not customer_id:
                violations.append("Account-specific request without customer authentication")
                required_actions.append("Verify customer identity before providing account information")
            else:
                required_actions.append("Confirm customer identity matches account access")
        
        # Check for high-risk operations
        high_risk_operations = [
            'close account', 'change address', 'add beneficiary', 'wire transfer',
            'large withdrawal', 'credit limit increase'
        ]
        
        if any(operation in query_lower for operation in high_risk_operations):
            required_actions.append("Enhanced authentication required for high-risk operation")
        
        return {
            'violations': violations,
            'required_actions': required_actions
        }
    
    def _check_transaction_compliance(self, query: str) -> Dict[str, List[str]]:
        """Check transaction-specific compliance requirements"""
        warnings = []
        required_actions = []
        
        query_lower = query.lower()
        
        # Check for transaction amount thresholds
        amount_patterns = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', query)
        for amount_str in amount_patterns:
            try:
                amount = float(amount_str.replace(',', ''))
                if amount >= 10000:
                    warnings.append(f"Transaction amount ${amount:,.2f} may require CTR filing")
                    required_actions.append("Review BSA reporting requirements")
                elif amount >= 3000:
                    warnings.append(f"Transaction amount ${amount:,.2f} may require enhanced monitoring")
            except ValueError:
                pass
        
        # Check for international transactions
        international_indicators = [
            'international', 'foreign', 'overseas', 'wire transfer', 'swift',
            'correspondent bank', 'cross-border'
        ]
        if any(indicator in query_lower for indicator in international_indicators):
            warnings.append("International transaction may require additional compliance checks")
            required_actions.append("Verify OFAC sanctions screening")
        
        # Check for business transactions
        business_indicators = [
            'business account', 'commercial', 'corporate', 'company', 'llc', 'inc'
        ]
        if any(indicator in query_lower for indicator in business_indicators):
            required_actions.append("Verify beneficial ownership information")
        
        return {
            'warnings': warnings,
            'required_actions': required_actions
        }
    
    def _generate_compliance_guidance(self, 
                                    violations: List[str],
                                    warnings: List[str],
                                    required_actions: List[str],
                                    escalation_required: bool) -> str:
        """Generate compliance guidance based on check results"""
        
        if violations:
            guidance = "COMPLIANCE VIOLATION DETECTED: "
            guidance += "This query contains potential compliance violations that must be addressed immediately. "
            guidance += "Do not proceed without proper compliance review and approval."
        
        elif escalation_required:
            guidance = "ESCALATION REQUIRED: "
            guidance += "This query involves complex regulatory requirements that require human review. "
            guidance += "Escalate to compliance team before proceeding."
        
        elif warnings or required_actions:
            guidance = "COMPLIANCE CAUTION: "
            guidance += "This query has compliance considerations that must be addressed. "
            guidance += "Ensure all regulatory requirements are met before proceeding."
        
        else:
            guidance = "COMPLIANT: "
            guidance += "This query appears to be compliant with banking regulations. "
            guidance += "Proceed with standard banking practices and security measures."
        
        # Add specific guidance for required actions
        if required_actions:
            guidance += f" Required actions: {'; '.join(required_actions[:3])}."
        
        return guidance
    
    def validate_response(self, response: str, query: str) -> Dict[str, Any]:
        """Validate agent response for compliance"""
        try:
            issues = []
            recommendations = []
            
            # Check for sensitive data in response
            sensitive_check = self._check_sensitive_data(response)
            if sensitive_check['violations'] or sensitive_check['warnings']:
                issues.extend(sensitive_check['violations'])
                issues.extend(sensitive_check['warnings'])
                recommendations.append("Remove or mask sensitive information in response")
            
            # Check for appropriate disclaimers
            response_lower = response.lower()
            
            # Financial advice disclaimer
            advice_indicators = ['recommend', 'suggest', 'should', 'invest', 'financial advice']
            if any(indicator in response_lower for indicator in advice_indicators):
                if 'not financial advice' not in response_lower and 'consult' not in response_lower:
                    recommendations.append("Include appropriate financial advice disclaimer")
            
            # FDIC insurance mention
            if 'deposit' in response_lower or 'savings' in response_lower:
                if 'fdic' not in response_lower:
                    recommendations.append("Consider mentioning FDIC insurance protection")
            
            # Privacy notice
            if 'personal information' in response_lower or 'data' in response_lower:
                if 'privacy' not in response_lower:
                    recommendations.append("Include privacy protection notice")
            
            return {
                'compliant': len(issues) == 0,
                'issues': issues,
                'recommendations': recommendations,
                'confidence': 0.9 if len(issues) == 0 else 0.6
            }
            
        except Exception as e:
            self.logger.error(f"Error validating response: {str(e)}")
            return {
                'compliant': False,
                'issues': [f"Validation error: {str(e)}"],
                'recommendations': ["Manual compliance review required"],
                'confidence': 0.0
            }
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get summary of compliance rules and requirements"""
        return {
            'compliance_rules': {
                name: {
                    'description': rule['description'],
                    'trigger_count': len(rule['triggers']),
                    'action_count': len(rule['required_actions'])
                }
                for name, rule in self.compliance_rules.items()
            },
            'sensitive_patterns': {
                name: {
                    'description': pattern['description'],
                    'risk_level': pattern['risk_level']
                }
                for name, pattern in self.sensitive_patterns.items()
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get compliance checker status"""
        return {
            "module": "compliance",
            "status": "healthy",
            "rules_loaded": len(self.compliance_rules),
            "patterns_loaded": len(self.sensitive_patterns),
            "capabilities": [
                "regulatory_compliance",
                "sensitive_data_detection",
                "authentication_validation",
                "transaction_monitoring",
                "response_validation"
            ],
            "compliance_areas": list(self.compliance_rules.keys())
        }

