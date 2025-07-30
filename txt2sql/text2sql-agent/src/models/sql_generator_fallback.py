"""
Fallback SQL Generator for Text-to-SQL Agent

This module provides SQL generation capabilities without requiring OpenAI API,
using pattern matching and template-based approaches for common retail queries.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class FallbackQueryContext:
    """Context for fallback SQL generation"""
    table_schemas: Dict[str, Any]
    available_tables: List[str]
    question: str
    entities: List[str]
    intent: str


@dataclass
class FallbackGeneratedSQL:
    """Generated SQL result from fallback generator"""
    sql_query: str
    confidence_score: float
    explanation: str
    tables_used: List[str]
    validation_errors: List[str]


class FallbackSQLGenerator:
    """Fallback SQL generator using pattern matching and templates"""
    
    def __init__(self):
        """Initialize the fallback SQL generator"""
        self.logger = logging.getLogger(__name__)
        
        # Define query patterns and templates
        self.query_patterns = self._initialize_patterns()
        
        # Common table mappings
        self.table_mappings = {
            'product': 'products',
            'pricing': 'pricing',
            'price': 'pricing',
            'elasticity': 'elasticity',
            'competitive': 'competitive_pricing',
            'competitor': 'competitive_pricing',
            'sales': 'sales_data',
            'revenue': 'sales_data',
            'margin': 'margin_analysis',
            'profit': 'margin_analysis',
            'store': 'stores'
        }
        
        # Category mappings
        self.category_mappings = {
            'frozen food': 'FROZEN FOOD',
            'dairy': 'DAIRY',
            'bread': 'BREAD & WRAPS',
            'beverages': 'BEVERAGES',
            'snacks': 'SNACKS',
            'meat': 'MEAT & SEAFOOD',
            'produce': 'PRODUCE',
            'bakery': 'BAKERY'
        }
        
        self.logger.info("Fallback SQL generator initialized")
    
    def _initialize_patterns(self) -> Dict[str, Dict]:
        """Initialize query patterns and templates"""
        return {
            'current_price_upc': {
                'pattern': r'current price.*upc.*[\'"]?([0-9]+)[\'"]?',
                'template': """
                SELECT p.product_name, pr.current_price, pr.price_date
                FROM products p 
                JOIN pricing pr ON p.upc_code = pr.upc_code 
                WHERE p.upc_code = '{upc_code}' 
                ORDER BY pr.price_date DESC 
                LIMIT 1
                """,
                'confidence': 0.8,
                'tables': ['products', 'pricing']
            },
            'top_elasticity_category': {
                'pattern': r'top\s+(\d+).*elasticity.*(frozen food|dairy|bread|beverages|snacks|meat|produce|bakery)',
                'template': """
                SELECT p.product_name, e.elasticity_value, p.category_level_2
                FROM products p 
                JOIN elasticity e ON p.upc_code = e.upc_code 
                WHERE UPPER(p.category_level_2) LIKE '%{category}%'
                ORDER BY e.elasticity_value DESC 
                LIMIT {limit}
                """,
                'confidence': 0.7,
                'tables': ['products', 'elasticity']
            },
            'cpi_higher_than': {
                'pattern': r'cpi.*higher.*than\s+(\d+\.?\d*)',
                'template': """
                SELECT p.product_name, cp.competitor_name, cp.cpi_value, cp.our_price, cp.competitor_price
                FROM products p 
                JOIN competitive_pricing cp ON p.upc_code = cp.upc_code 
                WHERE cp.cpi_value > {threshold}
                ORDER BY cp.cpi_value DESC 
                LIMIT 20
                """,
                'confidence': 0.7,
                'tables': ['products', 'competitive_pricing']
            },
            'revenue_by_category': {
                'pattern': r'revenue.*category.*(last|past)\s+(\d+)\s+(month|week)',
                'template': """
                SELECT p.category_level_2, SUM(s.revenue) as total_revenue, COUNT(DISTINCT p.upc_code) as product_count
                FROM products p 
                JOIN sales_data s ON p.upc_code = s.upc_code 
                WHERE s.week_ending_date >= date('now', '-{period} {unit}')
                GROUP BY p.category_level_2 
                ORDER BY total_revenue DESC
                """,
                'confidence': 0.6,
                'tables': ['products', 'sales_data']
            },
            'negative_margins': {
                'pattern': r'negative.*margin|margin.*negative|lowest.*margin',
                'template': """
                SELECT p.product_name, m.margin_percent, m.margin_amount, m.selling_price, m.cost
                FROM products p 
                JOIN margin_analysis m ON p.upc_code = m.upc_code 
                WHERE m.margin_percent < 0 OR m.margin_amount < 0
                ORDER BY m.margin_percent ASC 
                LIMIT 20
                """,
                'confidence': 0.8,
                'tables': ['products', 'margin_analysis']
            },
            'pricing_strategy_category_banner': {
                'pattern': r'pricing.*strateg.*(bread|dairy|frozen|beverages|snacks|meat|produce|bakery).*(banner|zone)\s*(\d+|[a-z]+)',
                'template': """
                SELECT p.product_name, pr.pricing_strategy, pr.current_price, pr.suggested_price, s.banner
                FROM products p 
                JOIN pricing pr ON p.upc_code = pr.upc_code 
                JOIN stores s ON pr.store_id = s.store_id
                WHERE UPPER(p.category_level_2) LIKE '%{category}%' 
                AND UPPER(s.banner) LIKE '%{banner}%'
                ORDER BY pr.price_date DESC
                LIMIT 50
                """,
                'confidence': 0.6,
                'tables': ['products', 'pricing', 'stores']
            },
            'average_price_category': {
                'pattern': r'average.*price.*(frozen food|dairy|bread|beverages|snacks|meat|produce|bakery)',
                'template': """
                SELECT p.category_level_2, AVG(pr.current_price) as avg_price, COUNT(*) as product_count
                FROM products p 
                JOIN pricing pr ON p.upc_code = pr.upc_code 
                WHERE UPPER(p.category_level_2) LIKE '%{category}%'
                GROUP BY p.category_level_2
                """,
                'confidence': 0.7,
                'tables': ['products', 'pricing']
            },
            'highest_revenue_stores': {
                'pattern': r'highest.*revenue.*store|store.*highest.*revenue',
                'template': """
                SELECT s.store_name, s.banner, SUM(sd.revenue) as total_revenue
                FROM stores s 
                JOIN sales_data sd ON s.store_id = sd.store_id 
                WHERE sd.week_ending_date >= date('now', '-1 month')
                GROUP BY s.store_id, s.store_name, s.banner
                ORDER BY total_revenue DESC 
                LIMIT 10
                """,
                'confidence': 0.7,
                'tables': ['stores', 'sales_data']
            },
            'competitive_pricing_product': {
                'pattern': r'competitive.*pricing.*(wonder bread|coca cola|pepsi|milk|cheese)',
                'template': """
                SELECT p.product_name, cp.competitor_name, cp.our_price, cp.competitor_price, cp.price_gap
                FROM products p 
                JOIN competitive_pricing cp ON p.upc_code = cp.upc_code 
                WHERE UPPER(p.product_name) LIKE '%{product}%'
                ORDER BY cp.observation_date DESC
                LIMIT 20
                """,
                'confidence': 0.6,
                'tables': ['products', 'competitive_pricing']
            }
        }
    
    def _extract_entities(self, question: str) -> Dict[str, Any]:
        """Extract entities from the question"""
        entities = {}
        question_lower = question.lower()
        
        # Extract UPC codes
        upc_match = re.search(r'[\'"]?([0-9]{10,})[\'"]?', question)
        if upc_match:
            entities['upc_code'] = upc_match.group(1)
        
        # Extract numbers (limits, thresholds)
        number_matches = re.findall(r'\b(\d+\.?\d*)\b', question)
        if number_matches:
            entities['numbers'] = [float(n) for n in number_matches]
        
        # Extract categories
        for category_key, category_value in self.category_mappings.items():
            if category_key in question_lower:
                entities['category'] = category_value
                break
        
        # Extract time periods
        time_match = re.search(r'(last|past)\s+(\d+)\s+(month|week|day)', question_lower)
        if time_match:
            entities['time_period'] = {
                'direction': time_match.group(1),
                'amount': int(time_match.group(2)),
                'unit': time_match.group(3)
            }
        
        # Extract banners/zones
        banner_match = re.search(r'banner\s*(\d+|[a-z]+)', question_lower)
        if banner_match:
            entities['banner'] = banner_match.group(1).upper()
        
        return entities
    
    def _match_pattern(self, question: str) -> Tuple[Optional[str], Optional[Dict], Dict[str, Any]]:
        """Match question against known patterns"""
        question_lower = question.lower()
        entities = self._extract_entities(question)
        
        for pattern_name, pattern_info in self.query_patterns.items():
            match = re.search(pattern_info['pattern'], question_lower)
            if match:
                self.logger.debug(f"Matched pattern: {pattern_name}")
                return pattern_name, pattern_info, entities
        
        return None, None, entities
    
    def _build_sql_from_template(self, template: str, entities: Dict[str, Any], match_groups: List[str] = None) -> str:
        """Build SQL query from template and entities"""
        sql = template.strip()
        
        # Replace common placeholders
        if 'upc_code' in entities:
            sql = sql.replace('{upc_code}', entities['upc_code'])
        
        if 'category' in entities:
            sql = sql.replace('{category}', entities['category'])
        
        if 'banner' in entities:
            sql = sql.replace('{banner}', entities['banner'])
        
        # Handle numbers for limits and thresholds
        if 'numbers' in entities and entities['numbers']:
            # Use first number as limit, second as threshold if available
            numbers = entities['numbers']
            if '{limit}' in sql:
                limit = int(numbers[0]) if numbers else 10
                sql = sql.replace('{limit}', str(limit))
            if '{threshold}' in sql:
                threshold = numbers[0] if numbers else 1.0
                sql = sql.replace('{threshold}', str(threshold))
        
        # Handle time periods
        if 'time_period' in entities:
            period_info = entities['time_period']
            sql = sql.replace('{period}', str(period_info['amount']))
            sql = sql.replace('{unit}', period_info['unit'] + 's')  # SQLite uses plural
        
        # Default replacements
        sql = sql.replace('{limit}', '10')
        sql = sql.replace('{threshold}', '1.0')
        sql = sql.replace('{period}', '6')
        sql = sql.replace('{unit}', 'months')
        sql = sql.replace('{category}', 'GROCERY')
        sql = sql.replace('{banner}', 'BANNER')
        sql = sql.replace('{product}', 'PRODUCT')
        
        return sql
    
    def _generate_generic_query(self, question: str, context: FallbackQueryContext) -> FallbackGeneratedSQL:
        """Generate a generic query when no specific pattern matches"""
        question_lower = question.lower()
        
        # Determine primary table based on keywords
        if any(word in question_lower for word in ['price', 'pricing', 'cost']):
            sql = """
            SELECT p.product_name, pr.current_price, pr.suggested_price, pr.pricing_strategy
            FROM products p 
            JOIN pricing pr ON p.upc_code = pr.upc_code 
            ORDER BY pr.price_date DESC 
            LIMIT 20
            """
            tables = ['products', 'pricing']
            explanation = "Generic pricing query - showing recent pricing data"
            
        elif any(word in question_lower for word in ['elasticity', 'elastic']):
            sql = """
            SELECT p.product_name, e.elasticity_value, e.elasticity_category, p.category_level_2
            FROM products p 
            JOIN elasticity e ON p.upc_code = e.upc_code 
            ORDER BY e.elasticity_value DESC 
            LIMIT 20
            """
            tables = ['products', 'elasticity']
            explanation = "Generic elasticity query - showing products by elasticity"
            
        elif any(word in question_lower for word in ['revenue', 'sales', 'sold']):
            sql = """
            SELECT p.product_name, SUM(s.revenue) as total_revenue, SUM(s.units_sold) as total_units
            FROM products p 
            JOIN sales_data s ON p.upc_code = s.upc_code 
            WHERE s.week_ending_date >= date('now', '-3 months')
            GROUP BY p.upc_code, p.product_name
            ORDER BY total_revenue DESC 
            LIMIT 20
            """
            tables = ['products', 'sales_data']
            explanation = "Generic sales query - showing revenue and units sold"
            
        elif any(word in question_lower for word in ['margin', 'profit']):
            sql = """
            SELECT p.product_name, m.margin_percent, m.margin_amount, m.selling_price
            FROM products p 
            JOIN margin_analysis m ON p.upc_code = m.upc_code 
            ORDER BY m.margin_percent DESC 
            LIMIT 20
            """
            tables = ['products', 'margin_analysis']
            explanation = "Generic margin query - showing profit margins"
            
        elif any(word in question_lower for word in ['competitor', 'competitive', 'cpi']):
            sql = """
            SELECT p.product_name, cp.competitor_name, cp.our_price, cp.competitor_price, cp.cpi_value
            FROM products p 
            JOIN competitive_pricing cp ON p.upc_code = p.upc_code 
            ORDER BY cp.cpi_value DESC 
            LIMIT 20
            """
            tables = ['products', 'competitive_pricing']
            explanation = "Generic competitive analysis query"
            
        else:
            # Default to product listing
            sql = """
            SELECT product_name, brand, category_level_2, base_price 
            FROM products 
            ORDER BY product_name 
            LIMIT 20
            """
            tables = ['products']
            explanation = "Generic product listing query"
        
        return FallbackGeneratedSQL(
            sql_query=sql,
            confidence_score=0.3,
            explanation=explanation,
            tables_used=tables,
            validation_errors=[]
        )
    
    def generate_sql(self, question: str, context: FallbackQueryContext) -> FallbackGeneratedSQL:
        """
        Generate SQL query using fallback pattern matching
        
        Args:
            question: Natural language question
            context: Query context with table schemas and metadata
            
        Returns:
            FallbackGeneratedSQL with query and metadata
        """
        try:
            self.logger.info(f"Generating fallback SQL for: {question}")
            
            # Try to match against known patterns
            pattern_name, pattern_info, entities = self._match_pattern(question)
            
            if pattern_name and pattern_info:
                # Build SQL from matched pattern
                sql_query = self._build_sql_from_template(
                    pattern_info['template'], 
                    entities
                )
                
                result = FallbackGeneratedSQL(
                    sql_query=sql_query,
                    confidence_score=pattern_info['confidence'],
                    explanation=f"Matched pattern: {pattern_name}",
                    tables_used=pattern_info['tables'],
                    validation_errors=[]
                )
                
                self.logger.info(f"Generated SQL using pattern: {pattern_name}")
                return result
            
            else:
                # Generate generic query
                result = self._generate_generic_query(question, context)
                self.logger.info("Generated generic fallback SQL")
                return result
                
        except Exception as e:
            self.logger.error(f"Error generating fallback SQL: {str(e)}")
            
            # Return a safe default query
            return FallbackGeneratedSQL(
                sql_query="SELECT product_name, brand, category_level_2 FROM products LIMIT 10",
                confidence_score=0.1,
                explanation=f"Error in SQL generation: {str(e)}",
                tables_used=['products'],
                validation_errors=[str(e)]
            )
    
    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Basic SQL validation for fallback queries
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            sql_lower = sql_query.lower().strip()
            
            # Check for dangerous operations
            forbidden_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
            for keyword in forbidden_keywords:
                if keyword in sql_lower:
                    return False, f"Forbidden keyword detected: {keyword}"
            
            # Check for basic SQL structure
            if not sql_lower.startswith('select'):
                return False, "Query must start with SELECT"
            
            # Check for required FROM clause
            if 'from' not in sql_lower:
                return False, "Query must contain FROM clause"
            
            # Basic syntax checks
            if sql_lower.count('(') != sql_lower.count(')'):
                return False, "Mismatched parentheses"
            
            if sql_lower.count("'") % 2 != 0:
                return False, "Mismatched single quotes"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_supported_patterns(self) -> List[Dict[str, Any]]:
        """Get list of supported query patterns"""
        patterns = []
        for name, info in self.query_patterns.items():
            patterns.append({
                'name': name,
                'pattern': info['pattern'],
                'confidence': info['confidence'],
                'tables': info['tables'],
                'description': f"Pattern for {name.replace('_', ' ')}"
            })
        return patterns


# Factory function
def create_fallback_sql_generator() -> FallbackSQLGenerator:
    """Create a fallback SQL generator instance"""
    return FallbackSQLGenerator()


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create fallback generator
    generator = create_fallback_sql_generator()
    
    # Test questions
    test_questions = [
        "What is the current price for UPC code '0020282000000'?",
        "Show me the top 10 items by elasticity in the frozen food category",
        "Which items have a CPI value higher than 1.05?",
        "Show me revenue by category for the last 6 months",
        "Which products have negative margins?",
        "What is the average price for products in the beverages category?",
        "Show me competitive pricing for Wonder Bread products"
    ]
    
    print("Testing Fallback SQL Generator:")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nTest {i}: {question}")
        print("-" * 30)
        
        # Create mock context
        context = FallbackQueryContext(
            table_schemas={},
            available_tables=['products', 'pricing', 'elasticity', 'competitive_pricing', 'sales_data', 'margin_analysis', 'stores'],
            question=question,
            entities=[],
            intent="general"
        )
        
        # Generate SQL
        result = generator.generate_sql(question, context)
        
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Tables: {', '.join(result.tables_used)}")
        print(f"Explanation: {result.explanation}")
        print(f"SQL: {result.sql_query[:100]}...")
        
        # Validate SQL
        is_valid, error = generator.validate_sql(result.sql_query)
        print(f"Valid: {is_valid}")
        if error:
            print(f"Error: {error}")
    
    print(f"\nSupported patterns: {len(generator.get_supported_patterns())}")
    print("Fallback SQL generator test completed!")

