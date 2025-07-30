"""
Query Processing Module for Text-to-SQL Agent

This module handles the initial processing of user questions including
entity extraction, intent classification, and question preprocessing.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from openai import OpenAI


@dataclass
class ExtractedEntity:
    """Represents an extracted entity from the question"""
    entity_type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int


@dataclass
class ProcessedQuestion:
    """Result of question processing"""
    original_question: str
    cleaned_question: str
    intent: str
    entities: List[ExtractedEntity]
    question_type: str
    complexity_score: float
    suggested_tables: List[str]
    parameters: Dict[str, Any]


class EntityExtractor:
    """Extracts entities from natural language questions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Entity patterns for retail analytics
        self.entity_patterns = {
            'upc_code': [
                r'\b\d{12,14}\b',  # Standard UPC codes
                r"'[0-9]{10,14}'",  # Quoted UPC codes
                r'"[0-9]{10,14}"',  # Double quoted UPC codes
                r'UPC\s*(?:code\s*)?[\'"]?([0-9]{10,14})[\'"]?',
                r'product\s*(?:code\s*)?[\'"]?([0-9]{10,14})[\'"]?'
            ],
            'date': [
                r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY
                r'week\s+ending\s+[\'"]?(\d{4}-\d{2}-\d{2})[\'"]?',
                r'for\s+the\s+week\s+ending\s+[\'"]?(\d{4}-\d{2}-\d{2})[\'"]?'
            ],
            'zone': [
                r'zone\s+[\'"]?([^\'"\s,]+)[\'"]?',
                r'in\s+zone\s+[\'"]?([^\'"\s,]+)[\'"]?',
                r'Banner\s+\d+',
                r'CS\s+zone\d+',
                r'Orange',
                r'Mich-High'
            ],
            'category': [
                r'level\s+2\s+[\'"]?([^\'"\n,]+)[\'"]?',
                r'category\s+[\'"]?([^\'"\n,]+)[\'"]?',
                r'within\s+[\'"]?([^\'"\n,]+)[\'"]?',
                r'in\s+[\'"]?(BREAD\s*&\s*WRAPS|FROZEN\s*FOOD|GROCERY|SEAFOOD|BAKERY)[\'"]?'
            ],
            'price_family': [
                r'price\s+family\s+[\'"]?([^\'"\s,]+)[\'"]?',
                r'family\s+[\'"]?([^\'"\s,]+)[\'"]?'
            ],
            'product_group': [
                r'product\s+group\s+[\'"]?([^\'"\n,]+)[\'"]?',
                r'group\s+[\'"]?([^\'"\n,]+)[\'"]?',
                r'KVI',
                r'TOP360'
            ],
            'percentage': [
                r'(\d+(?:\.\d+)?)\s*%',
                r'(\d+(?:\.\d+)?)\s*percent'
            ],
            'number': [
                r'\b(\d+(?:\.\d+)?)\b'
            ],
            'time_period': [
                r'last\s+(\d+)\s+(day|week|month|year)s?',
                r'past\s+(\d+)\s+(day|week|month|year)s?',
                r'in\s+(April|May|June|July|August|September|October|November|December)\s*(\d{4})?',
                r'since\s+[\'"]?(\d{4}-\d{2}-\d{2})[\'"]?'
            ]
        }
    
    def extract_entities(self, question: str) -> List[ExtractedEntity]:
        """Extract entities from the question"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, question, re.IGNORECASE)
                for match in matches:
                    # Extract the actual value (use group 1 if it exists, otherwise group 0)
                    value = match.group(1) if match.groups() else match.group(0)
                    
                    entity = ExtractedEntity(
                        entity_type=entity_type,
                        value=value.strip('\'"'),
                        confidence=0.9,  # High confidence for regex matches
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)
        
        # Remove duplicates and overlapping entities
        entities = self._remove_overlapping_entities(entities)
        
        return entities
    
    def _remove_overlapping_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove overlapping entities, keeping the most specific ones"""
        if not entities:
            return entities
        
        # Sort by start position
        entities.sort(key=lambda x: x.start_pos)
        
        filtered_entities = []
        for entity in entities:
            # Check if this entity overlaps with any already added entity
            overlaps = False
            for existing in filtered_entities:
                if (entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    # Keep the more specific entity (longer or higher confidence)
                    if (entity.end_pos - entity.start_pos > existing.end_pos - existing.start_pos or
                        entity.confidence > existing.confidence):
                        filtered_entities.remove(existing)
                        break
                    else:
                        overlaps = True
                        break
            
            if not overlaps:
                filtered_entities.append(entity)
        
        return filtered_entities


class IntentClassifier:
    """Classifies the intent of user questions"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client
        self.logger = logging.getLogger(__name__)
        
        # Intent patterns for quick classification
        self.intent_patterns = {
            'price_lookup': [
                'what is the price', 'current price', 'price for', 'cost of',
                'how much', 'price of'
            ],
            'price_analysis': [
                'price change', 'price recommendation', 'suggested price',
                'price impact', 'pricing strategy', 'price family'
            ],
            'elasticity_analysis': [
                'elasticity', 'elastic', 'price sensitive', 'demand response',
                'units impact', 'revenue impact', 'lift'
            ],
            'competitive_analysis': [
                'competitor', 'competitive', 'cpi', 'competitive price index',
                'market position', 'price gap', 'cp unit price'
            ],
            'sales_analysis': [
                'sales', 'revenue', 'units sold', 'volume', 'performance',
                'top selling', 'best selling', 'highest', 'lowest'
            ],
            'margin_analysis': [
                'margin', 'profit', 'profitability', 'cost analysis',
                'unit profit', 'gross margin'
            ],
            'forecast_analysis': [
                'forecast', 'prediction', 'projected', 'expected',
                'future', 'trend'
            ],
            'comparison': [
                'compare', 'comparison', 'versus', 'vs', 'difference',
                'between', 'against'
            ],
            'ranking': [
                'top', 'bottom', 'highest', 'lowest', 'best', 'worst',
                'rank', 'ranking', 'list'
            ],
            'aggregation': [
                'total', 'sum', 'average', 'count', 'number of',
                'how many', 'aggregate'
            ]
        }
    
    def classify_intent(self, question: str, entities: List[ExtractedEntity]) -> str:
        """Classify the intent of the question"""
        question_lower = question.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Boost scores based on entities
        entity_types = [e.entity_type for e in entities]
        
        if 'upc_code' in entity_types:
            intent_scores['price_lookup'] = intent_scores.get('price_lookup', 0) + 2
        
        if 'percentage' in entity_types:
            intent_scores['elasticity_analysis'] = intent_scores.get('elasticity_analysis', 0) + 1
            intent_scores['margin_analysis'] = intent_scores.get('margin_analysis', 0) + 1
        
        if 'time_period' in entity_types or 'date' in entity_types:
            intent_scores['forecast_analysis'] = intent_scores.get('forecast_analysis', 0) + 1
            intent_scores['sales_analysis'] = intent_scores.get('sales_analysis', 0) + 1
        
        # Return the highest scoring intent
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return 'general_query'
    
    def classify_with_llm(self, question: str) -> str:
        """Use LLM for more sophisticated intent classification"""
        if not self.client:
            return 'general_query'
        
        try:
            system_prompt = """You are an expert at classifying retail analytics questions. 
            Classify the following question into one of these categories:
            
            - price_lookup: Simple price queries for specific products
            - price_analysis: Complex pricing analysis, recommendations, strategies
            - elasticity_analysis: Price elasticity and demand sensitivity analysis
            - competitive_analysis: Competitor pricing and market position analysis
            - sales_analysis: Sales performance, volume, and revenue analysis
            - margin_analysis: Profit margin and cost analysis
            - forecast_analysis: Future predictions and trend analysis
            - comparison: Comparing products, categories, or time periods
            - ranking: Top/bottom lists and rankings
            - aggregation: Totals, averages, counts
            - general_query: Other types of questions
            
            Return only the category name."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error in LLM intent classification: {str(e)}")
            return 'general_query'


class QuestionProcessor:
    """Main question processing class"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.entity_extractor = EntityExtractor()
        self.intent_classifier = IntentClassifier(openai_client)
        self.logger = logging.getLogger(__name__)
        
        # Table suggestions based on intent and entities
        self.table_suggestions = {
            'price_lookup': ['products', 'pricing', 'current_prices'],
            'price_analysis': ['pricing', 'price_recommendations', 'price_changes', 'price_families'],
            'elasticity_analysis': ['elasticity', 'demand_analysis', 'price_sensitivity'],
            'competitive_analysis': ['competitor_prices', 'cpi_analysis', 'market_data'],
            'sales_analysis': ['sales', 'revenue', 'units_sold', 'performance'],
            'margin_analysis': ['margins', 'costs', 'profitability'],
            'forecast_analysis': ['forecasts', 'predictions', 'trends'],
            'comparison': ['products', 'categories', 'time_series'],
            'ranking': ['products', 'categories', 'performance'],
            'aggregation': ['sales', 'products', 'categories']
        }
    
    def process_question(self, question: str) -> ProcessedQuestion:
        """
        Process a natural language question
        
        Args:
            question: The user's natural language question
            
        Returns:
            ProcessedQuestion object with extracted information
        """
        try:
            # Clean the question
            cleaned_question = self._clean_question(question)
            
            # Extract entities
            entities = self.entity_extractor.extract_entities(cleaned_question)
            
            # Classify intent
            intent = self.intent_classifier.classify_intent(cleaned_question, entities)
            
            # Determine question type and complexity
            question_type = self._determine_question_type(cleaned_question, entities)
            complexity_score = self._calculate_complexity(cleaned_question, entities)
            
            # Suggest relevant tables
            suggested_tables = self._suggest_tables(intent, entities)
            
            # Extract parameters
            parameters = self._extract_parameters(entities)
            
            return ProcessedQuestion(
                original_question=question,
                cleaned_question=cleaned_question,
                intent=intent,
                entities=entities,
                question_type=question_type,
                complexity_score=complexity_score,
                suggested_tables=suggested_tables,
                parameters=parameters
            )
            
        except Exception as e:
            self.logger.error(f"Error processing question: {str(e)}")
            return ProcessedQuestion(
                original_question=question,
                cleaned_question=question,
                intent='error',
                entities=[],
                question_type='error',
                complexity_score=0.0,
                suggested_tables=[],
                parameters={}
            )
    
    def _clean_question(self, question: str) -> str:
        """Clean and normalize the question"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', question.strip())
        
        # Normalize quotes
        cleaned = re.sub(r'[""''`]', '"', cleaned)
        
        # Normalize common abbreviations
        replacements = {
            r'\bUPC\b': 'UPC code',
            r'\bCPI\b': 'competitive price index',
            r'\bCP\b': 'competitor price',
            r'\bPLG\b': 'price lookup group',
            r'\bKVI\b': 'key value item'
        }
        
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _determine_question_type(self, question: str, entities: List[ExtractedEntity]) -> str:
        """Determine the type of question (simple, complex, analytical)"""
        question_lower = question.lower()
        
        # Simple questions
        simple_indicators = ['what is', 'show me', 'list', 'get']
        if any(indicator in question_lower for indicator in simple_indicators):
            if len(entities) <= 2:
                return 'simple'
        
        # Complex analytical questions
        complex_indicators = [
            'impact', 'analysis', 'compare', 'trend', 'forecast',
            'optimization', 'recommendation', 'strategy'
        ]
        if any(indicator in question_lower for indicator in complex_indicators):
            return 'analytical'
        
        # Multi-part questions
        if '?' in question[:-1] or len(question.split(',')) > 2:
            return 'multi_part'
        
        return 'standard'
    
    def _calculate_complexity(self, question: str, entities: List[ExtractedEntity]) -> float:
        """Calculate complexity score (0.0 to 1.0)"""
        score = 0.0
        
        # Base complexity from question length
        score += min(len(question.split()) / 50.0, 0.3)
        
        # Entity complexity
        score += min(len(entities) / 10.0, 0.2)
        
        # Keyword complexity
        complex_keywords = [
            'analysis', 'optimization', 'recommendation', 'strategy',
            'forecast', 'prediction', 'trend', 'correlation',
            'elasticity', 'sensitivity', 'impact'
        ]
        
        keyword_count = sum(1 for keyword in complex_keywords 
                          if keyword in question.lower())
        score += min(keyword_count / 5.0, 0.3)
        
        # Aggregation complexity
        aggregation_keywords = ['sum', 'average', 'count', 'total', 'group by']
        if any(keyword in question.lower() for keyword in aggregation_keywords):
            score += 0.2
        
        return min(score, 1.0)
    
    def _suggest_tables(self, intent: str, entities: List[ExtractedEntity]) -> List[str]:
        """Suggest relevant tables based on intent and entities"""
        suggested = set(self.table_suggestions.get(intent, []))
        
        # Add tables based on entities
        entity_types = [e.entity_type for e in entities]
        
        if 'upc_code' in entity_types:
            suggested.update(['products', 'pricing'])
        
        if 'zone' in entity_types:
            suggested.update(['zones', 'regional_data'])
        
        if 'category' in entity_types:
            suggested.update(['categories', 'product_hierarchy'])
        
        if 'date' in entity_types or 'time_period' in entity_types:
            suggested.update(['time_series', 'historical_data'])
        
        return list(suggested)
    
    def _extract_parameters(self, entities: List[ExtractedEntity]) -> Dict[str, Any]:
        """Extract parameters from entities"""
        parameters = {}
        
        for entity in entities:
            if entity.entity_type == 'date':
                parameters['date'] = entity.value
            elif entity.entity_type == 'upc_code':
                parameters['upc_code'] = entity.value
            elif entity.entity_type == 'zone':
                parameters['zone'] = entity.value
            elif entity.entity_type == 'category':
                parameters['category'] = entity.value
            elif entity.entity_type == 'price_family':
                parameters['price_family'] = entity.value
            elif entity.entity_type == 'percentage':
                parameters['percentage'] = float(entity.value)
            elif entity.entity_type == 'time_period':
                parameters['time_period'] = entity.value
        
        return parameters


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Test question processing
    processor = QuestionProcessor()
    
    test_questions = [
        "What is the current price for UPC code '0020282000000'?",
        "Show me the top 10 items by elasticity in the frozen food category",
        "What are the pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'?",
        "How many price increases were there in April 2025?",
        "What is the impact on margin if I create a minimum price gap of 1% on 'C' products?"
    ]
    
    for question in test_questions:
        result = processor.process_question(question)
        print(f"\nQuestion: {question}")
        print(f"Intent: {result.intent}")
        print(f"Entities: {[(e.entity_type, e.value) for e in result.entities]}")
        print(f"Complexity: {result.complexity_score:.2f}")
        print(f"Suggested tables: {result.suggested_tables}")

