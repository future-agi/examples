"""
SQL Generation Module for Text-to-SQL Agent

This module handles the conversion of natural language questions to SQL queries
using OpenAI's GPT-4o model with sophisticated prompt engineering.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from openai import OpenAI
import sqlparse
from sqlparse import sql, tokens

from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType
from traceai_openai import OpenAIInstrumentor
from opentelemetry import trace
from fi.evals import Evaluator
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import (
    ProjectType
)
from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

from fi.evals import Evaluator
evaluator = Evaluator(fi_api_key=os.getenv("FI_API_KEY"), fi_secret_key=os.getenv("FI_SECRET_KEY"))

tracer = FITracer(trace.get_tracer(__name__))

@dataclass
class QueryContext:
    """Context information for SQL generation"""
    table_schemas: Dict[str, Any]
    sample_data: Dict[str, List[Dict]]
    business_rules: List[str]
    similar_queries: List[Dict[str, str]]
    metadata: Dict[str, Any]


@dataclass
class GeneratedSQL:
    """Result of SQL generation"""
    sql_query: str
    confidence_score: float
    explanation: str
    tables_used: List[str]
    columns_used: List[str]
    query_type: str
    validation_errors: List[str]


class SQLValidator:
    """Validates generated SQL queries for safety and correctness"""
    
    FORBIDDEN_KEYWORDS = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE',
        'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'CALL', 'MERGE'
    ]
    
    ALLOWED_FUNCTIONS = [
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'CAST', 'COALESCE',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'EXTRACT', 'DATE_TRUNC',
        'UPPER', 'LOWER', 'SUBSTRING', 'LENGTH', 'TRIM', 'CONCAT'
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_query(self, sql_query: str) -> Tuple[bool, List[str]]:
        with tracer.start_as_current_span("validate_query") as span:
            span.set_attribute("validate_query", "validate_query")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", sql_query)

            """
            Validate SQL query for safety and correctness
            
            Args:
                sql_query: The SQL query to validate
                
            Returns:
                Tuple of (is_valid, list_of_errors)
            """
            errors = []
            
            try:
                # Parse the SQL query
                parsed = sqlparse.parse(sql_query)
                if not parsed:
                    errors.append("Unable to parse SQL query")
                    return False, errors
                
                # Check for forbidden keywords
                sql_upper = sql_query.upper()
                for keyword in self.FORBIDDEN_KEYWORDS:
                    if keyword in sql_upper:
                        errors.append(f"Forbidden keyword detected: {keyword}")
                
                # Check for basic SQL injection patterns
                injection_patterns = [
                    r";\s*(DROP|DELETE|INSERT|UPDATE)",
                    r"UNION\s+SELECT",
                    r"--\s*$",
                    r"/\*.*\*/"
                ]
                
                for pattern in injection_patterns:
                    if re.search(pattern, sql_upper):
                        errors.append(f"Potential SQL injection pattern detected: {pattern}")
                
                # Validate query structure
                statement = parsed[0]
                if not self._is_select_query(statement):
                    errors.append("Only SELECT queries are allowed")
                
                # Check for reasonable complexity (prevent overly complex queries)
                if sql_query.count('(') > 10:
                    errors.append("Query complexity exceeds maximum allowed nesting")
                
                span.set_attribute("output.value", len(errors)==0)
                return len(errors) == 0, errors
                
            except Exception as e:
                errors.append(f"SQL validation error: {str(e)}")
                return False, errors
    
    def _is_select_query(self, statement) -> bool:
        with tracer.start_as_current_span("is_select_query") as span:
            span.set_attribute("is_select_query", "is_select_query")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", statement.value)
            span.set_attribute("output.value", True)

            """Check if the statement is a SELECT query"""
            for token in statement.flatten():
                if token.ttype is tokens.Keyword.DML and token.value.upper() == 'SELECT':
                    return True
            return False


class PromptTemplate:
    """Manages prompt templates for different types of queries"""
    
    BASE_SYSTEM_PROMPT = """You are an expert SQL analyst specializing in retail analytics and pricing data. 
Your task is to convert natural language questions into precise SQLite SQL queries.

IMPORTANT GUIDELINES:
1. Generate ONLY SELECT queries - no INSERT, UPDATE, DELETE, or DDL operations
2. Use proper SQLite syntax and functions
3. Include appropriate WHERE clauses for date filtering when dates are mentioned
4. Use table aliases for readability
5. Include LIMIT clauses for large result sets (default LIMIT 100 unless specified)
6. Handle NULL values appropriately with COALESCE or IS NULL/IS NOT NULL
7. Use proper aggregation functions (SUM, COUNT, AVG, etc.) when needed
8. Format dates using SQLite date functions like date() and datetime()
9. Use CASE statements for conditional logic
10. Include proper JOINs when multiple tables are needed
11. CRITICAL: Use the EXACT column names provided in the schema - do not assume column names
12. Pay attention to the actual table structure provided in the context

BUSINESS CONTEXT:
- UPC codes are product identifiers (stored as 'upc_code' column)
- Categories are hierarchical: category_level_1, category_level_2, category_level_3
- Price families group related products
- Zones represent different geographical or business areas
- Elasticity measures price sensitivity (>1 = elastic, <1 = inelastic)
- CPI = Competitive Price Index
- CP Unit Price = Competitor Price Unit Price

CRITICAL SCHEMA NOTES:
- Product identifiers use 'upc_code' NOT 'upc'
- Categories use 'category_level_1', 'category_level_2', 'category_level_3' NOT just 'category'
- Always check the provided schema for exact column names
- Join tables using the correct foreign key relationships

RESPONSE FORMAT:
Return a JSON object with:
{
    "sql_query": "your SQL query here",
    "explanation": "brief explanation of the query logic",
    "confidence": 0.95,
    "query_type": "pricing_analysis|elasticity_analysis|competitive_analysis|sales_analysis|general",
    "tables_used": ["table1", "table2"],
    "columns_used": ["col1", "col2"]
}"""

    PRICING_ANALYSIS_PROMPT = """
PRICING ANALYSIS CONTEXT:
Focus on current prices, suggested prices, price changes, and pricing strategies.
Common tables: products, pricing, price_recommendations, price_changes
Key columns: current_price, suggested_price, price_family, upc_code, zone
"""

    ELASTICITY_ANALYSIS_PROMPT = """
ELASTICITY ANALYSIS CONTEXT:
Focus on price elasticity, demand sensitivity, and unit impact analysis.
Common tables: elasticity, products, sales_forecast
Key columns: elasticity_value, confidence_score, units_impact, revenue_impact
"""

    COMPETITIVE_ANALYSIS_PROMPT = """
COMPETITIVE ANALYSIS CONTEXT:
Focus on competitor pricing, CPI analysis, and market positioning.
Common tables: competitor_prices, cpi_analysis, products
Key columns: cp_unit_price, cpi_value, competitor_name, price_gap
"""

    def get_system_prompt(self, query_type: str = "general") -> str:
        """Get system prompt based on query type"""
        base = self.BASE_SYSTEM_PROMPT
        
        if query_type == "pricing_analysis":
            return base + "\n" + self.PRICING_ANALYSIS_PROMPT
        elif query_type == "elasticity_analysis":
            return base + "\n" + self.ELASTICITY_ANALYSIS_PROMPT
        elif query_type == "competitive_analysis":
            return base + "\n" + self.COMPETITIVE_ANALYSIS_PROMPT
        
        return base


class SQLGenerator:
    """Main SQL generation class using OpenAI GPT-4o"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SQL Generator
        
        Args:
            api_key: OpenAI API key (uses environment variable if not provided)
        """
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.validator = SQLValidator()
        self.prompt_template = PromptTemplate()
        self.logger = logging.getLogger(__name__)
        
        # Query type classification patterns
        self.query_patterns = {
            'pricing_analysis': [
                'price', 'pricing', 'cost', 'margin', 'suggested price', 'current price',
                'price change', 'price recommendation', 'price family'
            ],
            'elasticity_analysis': [
                'elasticity', 'elastic', 'inelastic', 'price sensitive', 'demand',
                'units impact', 'revenue impact', 'lift'
            ],
            'competitive_analysis': [
                'competitor', 'competitive', 'cpi', 'competitive price index',
                'cp unit price', 'price gap', 'market position'
            ],
            'sales_analysis': [
                'sales', 'revenue', 'units', 'volume', 'forecast', 'performance',
                'top selling', 'bottom', 'highest', 'lowest'
            ]
        }
    
    def classify_query_type(self, question: str) -> str:
        with tracer.start_as_current_span("classify_query_type") as span:
            span.set_attribute("classify_query_type", "classify_query_type")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", question)

            """Classify the type of query based on keywords"""
            question_lower = question.lower()
            
            scores = {}
            for query_type, keywords in self.query_patterns.items():
                score = sum(1 for keyword in keywords if keyword in question_lower)
                if score > 0:
                    scores[query_type] = score
            
            if scores:
                span.set_attribute("output.value", max(scores, key=scores.get))
        
            
                return max(scores, key=scores.get)
            return "general"
    
    def generate_sql(self, question: str, context: QueryContext) -> GeneratedSQL:
        with tracer.start_as_current_span("generate_sql") as span:
            span.set_attribute("generate_sql", "generate_sql")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", question)

            """
            Generate SQL query from natural language question
            
            Args:
                question: Natural language question
                context: Query context with schema and metadata
                
            Returns:
                GeneratedSQL object with query and metadata
            """
            try:
                # Classify query type
                query_type = self.classify_query_type(question)
                
                # Build context-aware prompt
                system_prompt = self.prompt_template.get_system_prompt(query_type)
                user_prompt = self._build_user_prompt(question, context)
                
                # Generate SQL using GPT-4o
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent SQL generation
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                
                # Parse response
                result = json.loads(response.choices[0].message.content)
                
                # Validate generated SQL
                is_valid, validation_errors = self.validator.validate_query(result['sql_query'])
                
                # Create GeneratedSQL object
                generated_sql = GeneratedSQL(
                    sql_query=result['sql_query'],
                    confidence_score=result.get('confidence', 0.8),
                    explanation=result.get('explanation', ''),
                    tables_used=result.get('tables_used', []),
                    columns_used=result.get('columns_used', []),
                    query_type=result.get('query_type', query_type),
                    validation_errors=validation_errors
                )
                
                if not is_valid:
                    self.logger.warning(f"Generated SQL failed validation: {validation_errors}")
                    generated_sql.confidence_score *= 0.5  # Reduce confidence for invalid queries
                
                span.set_attribute("output.value", generated_sql.sql_query)
                span.set_attribute("tables_used.value", generated_sql.tables_used)
                config_text_to_sql = {
                    "eval_templates" : "text_to_sql",
                    "inputs" : {
                        "input": question,
                        "output": generated_sql.sql_query,
                    },
                    "model_name" : "turing_large"
                }
                eval_result1 = evaluator.evaluate(
                    **config_text_to_sql, 
                    custom_eval_name="text_to_sql", 
                    trace_eval=True
                )

                config_evaluate_function_calling = {
                    "eval_templates" : "evaluate_function_calling",
                    "inputs" : {
                        "input": question,
                        "output": json.dumps(generated_sql.tables_used),
                    },
                    "model_name" : "turing_large"
                }
                eval_result2 = evaluator.evaluate(
                    **config_evaluate_function_calling, 
                    custom_eval_name="evaluate_function_calling", 
                    trace_eval=True
                )

                config_sql_syntactic_correctness = {
                    "eval_templates" : "sql_syntactic_correctness",
                    "inputs" : {
                        "sql_query": generated_sql.sql_query,
                    },
                    "model_name" : "turing_large"
                }   
                eval_result3 = evaluator.evaluate(
                    **config_sql_syntactic_correctness, 
                    custom_eval_name="sql_syntactic_correctness", 
                    trace_eval=True
                )

                config_schema_adherence = {
                    "eval_templates" : "schema_adherence",
                    "inputs" : {
                        "schema_details": context.table_schemas,
                        "sql_query": generated_sql.sql_query,
                    },
                    "model_name" : "turing_large"
                }
                
                eval_result4 = evaluator.evaluate(
                    **config_schema_adherence,
                    custom_eval_name="schema_adherence", 
                    trace_eval=True
                )

                return generated_sql
            

                
            except Exception as e:
                self.logger.error(f"Error generating SQL: {str(e)}")
                return GeneratedSQL(
                    sql_query="",
                    confidence_score=0.0,
                    explanation=f"Error generating SQL: {str(e)}",
                    tables_used=[],
                    columns_used=[],
                    query_type="error",
                    validation_errors=[str(e)]
                )
    
    def _build_user_prompt(self, question: str, context: QueryContext) -> str:
        """Build user prompt with question and context"""
        prompt_parts = [
            f"QUESTION: {question}",
            "",
            "AVAILABLE TABLES AND SCHEMAS (USE EXACT COLUMN NAMES):"
        ]
        
        # Add table schemas with detailed information
        for table_name, schema in context.table_schemas.items():
            prompt_parts.append(f"\nTable: {table_name}")
            prompt_parts.append(f"Description: {schema.get('description', 'No description available')}")
            
            if isinstance(schema, dict) and 'columns' in schema:
                prompt_parts.append("Columns:")
                for col in schema['columns']:
                    col_info = f"  - {col['name']} ({col['type']})"
                    if col.get('description'):
                        col_info += f": {col['description']}"
                    # Add constraint information if available
                    if col.get('primary_key'):
                        col_info += " [PRIMARY KEY]"
                    if col.get('nullable') is False:
                        col_info += " [NOT NULL]"
                    prompt_parts.append(col_info)
            
            # Add sample data if available to show actual data patterns
            if isinstance(schema, dict) and schema.get('sample_data'):
                prompt_parts.append("Sample data (showing actual values):")
                for i, row in enumerate(schema['sample_data'][:2]):  # Show 2 sample rows
                    row_str = ", ".join([f"{k}='{v}'" for k, v in row.items() if v is not None])
                    prompt_parts.append(f"  Sample {i+1}: {row_str}")
        
        # Add database type context
        if context.metadata.get('database_type') == 'sqlite':
            prompt_parts.append("\nDATABASE: SQLite")
            prompt_parts.append("- Use SQLite-specific syntax")
            prompt_parts.append("- Date functions: date(), datetime(), strftime()")
            prompt_parts.append("- String functions: UPPER(), LOWER(), SUBSTR()")
        
        # Add available tables list
        if context.metadata.get('available_tables'):
            tables_list = ", ".join(context.metadata['available_tables'])
            prompt_parts.append(f"\nAvailable tables: {tables_list}")
        
        # Add business rules
        if context.business_rules:
            prompt_parts.append("\nBUSINESS RULES:")
            for rule in context.business_rules:
                prompt_parts.append(f"  - {rule}")
        
        # Add similar queries as examples
        if context.similar_queries:
            prompt_parts.append("\nSIMILAR QUERY EXAMPLES:")
            for example in context.similar_queries[:3]:
                prompt_parts.append(f"Q: {example.get('question', '')}")
                prompt_parts.append(f"A: {example.get('sql', '')}")
                prompt_parts.append("")
        
        # Add final reminders
        prompt_parts.append("\nREMEMBER:")
        prompt_parts.append("- Use EXACT column names as shown above")
        prompt_parts.append("- Check table relationships carefully")
        prompt_parts.append("- Use appropriate JOIN conditions")
        prompt_parts.append("- Include reasonable LIMIT clauses")
        
        return "\n".join(prompt_parts)
    
    def refine_sql(self, original_sql: str, feedback: str, context: QueryContext) -> GeneratedSQL:
        with tracer.start_as_current_span("refine_sql") as span:
            span.set_attribute("refine_sql", "refine_sql")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", "input")
            span.set_attribute("output.value", "output")

            """
            Refine SQL query based on feedback
            
            Args:
                original_sql: Original SQL query
                feedback: User feedback or error message
                context: Query context
                
            Returns:
                Refined GeneratedSQL object
            """
            try:
                system_prompt = """You are an expert SQL analyst. Your task is to refine and improve an existing SQL query based on feedback.
                
    GUIDELINES:
    1. Analyze the feedback carefully
    2. Identify the specific issues with the original query
    3. Generate an improved version that addresses the feedback
    4. Maintain the original intent while fixing the problems
    5. Follow all the same safety and syntax rules as before

    Return the same JSON format as before with the refined query."""

                user_prompt = f"""
    ORIGINAL SQL QUERY:
    {original_sql}

    FEEDBACK/ISSUES:
    {feedback}

    CONTEXT:
    {self._build_user_prompt("Refine the above query", context)}

    Please provide a refined SQL query that addresses the feedback while maintaining the original intent.
    """

                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                
                # Validate refined SQL
                is_valid, validation_errors = self.validator.validate_query(result['sql_query'])
                
                return GeneratedSQL(
                    sql_query=result['sql_query'],
                    confidence_score=result.get('confidence', 0.8),
                    explanation=result.get('explanation', ''),
                    tables_used=result.get('tables_used', []),
                    columns_used=result.get('columns_used', []),
                    query_type=result.get('query_type', 'refined'),
                    validation_errors=validation_errors
                )
                
            except Exception as e:
                self.logger.error(f"Error refining SQL: {str(e)}")
                return GeneratedSQL(
                    sql_query=original_sql,  # Return original if refinement fails
                    confidence_score=0.3,
                    explanation=f"Error refining SQL: {str(e)}",
                    tables_used=[],
                    columns_used=[],
                    query_type="error",
                    validation_errors=[str(e)]
                )


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Example context
    sample_context = QueryContext(
        table_schemas={
            "products": {
                "columns": [
                    {"name": "upc_code", "type": "STRING", "description": "Product UPC identifier"},
                    {"name": "product_name", "type": "STRING", "description": "Product description"},
                    {"name": "category", "type": "STRING", "description": "Product category"},
                    {"name": "price_family", "type": "STRING", "description": "Price family grouping"}
                ]
            },
            "pricing": {
                "columns": [
                    {"name": "upc_code", "type": "STRING", "description": "Product UPC identifier"},
                    {"name": "zone", "type": "STRING", "description": "Geographic zone"},
                    {"name": "current_price", "type": "FLOAT", "description": "Current retail price"},
                    {"name": "suggested_price", "type": "FLOAT", "description": "AI suggested price"},
                    {"name": "week_ending", "type": "DATE", "description": "Week ending date"}
                ]
            }
        },
        sample_data={},
        business_rules=[
            "UPC codes are unique product identifiers",
            "Zones represent different geographical areas",
            "Price families group similar products for pricing strategies"
        ],
        similar_queries=[],
        metadata={}
    )
    
    # Test SQL generation
    generator = SQLGenerator()
    question = "What is the current price for UPC code '0020282000000'?"
    
    result = generator.generate_sql(question, sample_context)
    print(f"Generated SQL: {result.sql_query}")
    print(f"Explanation: {result.explanation}")
    print(f"Confidence: {result.confidence_score}")

