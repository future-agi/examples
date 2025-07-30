"""
Fixed Vector Store Implementation for Text-to-SQL Agent

This module provides vector storage and retrieval capabilities using ChromaDB
with fixed metadata handling to resolve list-type metadata issues.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import chromadb
from chromadb.config import Settings
import hashlib


@dataclass
class TableSchema:
    """Database table schema information"""
    table_name: str
    columns: List[Dict[str, str]]
    description: str
    sample_data: Optional[List[Dict[str, Any]]] = None


@dataclass
class QueryExample:
    """Example query and SQL pair"""
    question: str
    sql_query: str
    description: str
    tables_used: List[str]
    difficulty: str = "medium"


@dataclass
class BusinessRule:
    """Business rule for query generation"""
    rule_id: str
    description: str
    applies_to: List[str]
    priority: str = "medium"


@dataclass
class RetrievedContext:
    """Context retrieved from vector store"""
    schemas: List[TableSchema]
    examples: List[QueryExample]
    rules: List[BusinessRule]
    metadata: Dict[str, Any]


class VectorStoreFixed:
    """Fixed vector store implementation with proper metadata handling"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the vector store
        
        Args:
            persist_directory: Directory to persist the vector database
        """
        self.persist_directory = persist_directory
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize collections
        self._initialize_collections()
        
        self.logger.info(f"Vector store initialized with directory: {persist_directory}")
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections"""
        try:
            # Schema collection
            self.schema_collection = self.client.get_or_create_collection(
                name="schemas",
                metadata={"description": "Database table schemas"}
            )
            
            # Examples collection
            self.examples_collection = self.client.get_or_create_collection(
                name="examples",
                metadata={"description": "Query examples"}
            )
            
            # Rules collection
            self.rules_collection = self.client.get_or_create_collection(
                name="rules",
                metadata={"description": "Business rules"}
            )
            
            self.logger.info("ChromaDB collections initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing collections: {str(e)}")
            raise
    
    def _serialize_list_metadata(self, data: Any) -> str:
        """Convert list/dict metadata to JSON string"""
        if isinstance(data, (list, dict)):
            return json.dumps(data)
        return str(data)
    
    def _deserialize_list_metadata(self, data: str) -> Any:
        """Convert JSON string back to list/dict"""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    def add_table_schema(self, schema: TableSchema):
        """Add table schema to vector store"""
        try:
            # Create document text for embedding
            doc_text = f"""
            Table: {schema.table_name}
            Description: {schema.description}
            Columns: {', '.join([f"{col['name']} ({col['type']})" for col in schema.columns])}
            """
            
            # Prepare metadata (serialize complex types)
            metadata = {
                "table_name": schema.table_name,
                "description": schema.description,
                "columns_json": self._serialize_list_metadata(schema.columns),
                "column_count": len(schema.columns),
                "type": "schema"
            }
            
            # Add sample data if available
            if schema.sample_data:
                metadata["sample_data_json"] = self._serialize_list_metadata(schema.sample_data)
                metadata["has_sample_data"] = True
            else:
                metadata["has_sample_data"] = False
            
            # Generate unique ID
            schema_id = f"schema_{schema.table_name}"
            
            # Add to collection
            self.schema_collection.add(
                documents=[doc_text.strip()],
                metadatas=[metadata],
                ids=[schema_id]
            )
            
            self.logger.debug(f"Added schema for table: {schema.table_name}")
            
        except Exception as e:
            self.logger.error(f"Error adding schema for {schema.table_name}: {str(e)}")
    
    def add_query_example(self, example: QueryExample):
        """Add query example to vector store"""
        try:
            # Create document text for embedding
            doc_text = f"""
            Question: {example.question}
            SQL: {example.sql_query}
            Description: {example.description}
            Tables: {', '.join(example.tables_used)}
            """
            
            # Prepare metadata (serialize complex types)
            metadata = {
                "question": example.question,
                "sql_query": example.sql_query,
                "description": example.description,
                "tables_used_json": self._serialize_list_metadata(example.tables_used),
                "difficulty": example.difficulty,
                "table_count": len(example.tables_used),
                "type": "example"
            }
            
            # Generate unique ID
            example_id = f"example_{hashlib.md5(example.question.encode()).hexdigest()[:8]}"
            
            # Add to collection
            self.examples_collection.add(
                documents=[doc_text.strip()],
                metadatas=[metadata],
                ids=[example_id]
            )
            
            self.logger.debug(f"Added query example: {example.question[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error adding example: {str(e)}")
    
    def add_business_rule(self, rule: BusinessRule):
        """Add business rule to vector store"""
        try:
            # Create document text for embedding
            doc_text = f"""
            Rule: {rule.description}
            Applies to: {', '.join(rule.applies_to)}
            Priority: {rule.priority}
            """
            
            # Prepare metadata (serialize complex types)
            metadata = {
                "rule_id": rule.rule_id,
                "description": rule.description,
                "applies_to_json": self._serialize_list_metadata(rule.applies_to),
                "priority": rule.priority,
                "scope_count": len(rule.applies_to),
                "type": "rule"
            }
            
            # Generate unique ID
            rule_id = f"rule_{rule.rule_id}"
            
            # Add to collection
            self.rules_collection.add(
                documents=[doc_text.strip()],
                metadatas=[metadata],
                ids=[rule_id]
            )
            
            self.logger.debug(f"Added business rule: {rule.rule_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding rule {rule.rule_id}: {str(e)}")
    
    def search_schemas(self, query: str, limit: int = 5) -> List[TableSchema]:
        """Search for relevant table schemas"""
        try:
            results = self.schema_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            schemas = []
            if results['metadatas'] and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    # Deserialize complex metadata
                    columns = self._deserialize_list_metadata(metadata.get('columns_json', '[]'))
                    sample_data = None
                    if metadata.get('has_sample_data', False):
                        sample_data = self._deserialize_list_metadata(metadata.get('sample_data_json', '[]'))
                    
                    schema = TableSchema(
                        table_name=metadata['table_name'],
                        columns=columns,
                        description=metadata['description'],
                        sample_data=sample_data
                    )
                    schemas.append(schema)
            
            return schemas
            
        except Exception as e:
            self.logger.error(f"Error searching schemas: {str(e)}")
            return []
    
    def search_examples(self, query: str, limit: int = 3) -> List[QueryExample]:
        """Search for relevant query examples"""
        try:
            results = self.examples_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            examples = []
            if results['metadatas'] and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    # Deserialize complex metadata
                    tables_used = self._deserialize_list_metadata(metadata.get('tables_used_json', '[]'))
                    
                    example = QueryExample(
                        question=metadata['question'],
                        sql_query=metadata['sql_query'],
                        description=metadata['description'],
                        tables_used=tables_used,
                        difficulty=metadata.get('difficulty', 'medium')
                    )
                    examples.append(example)
            
            return examples
            
        except Exception as e:
            self.logger.error(f"Error searching examples: {str(e)}")
            return []
    
    def search_rules(self, query: str, limit: int = 5) -> List[BusinessRule]:
        """Search for relevant business rules"""
        try:
            results = self.rules_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            rules = []
            if results['metadatas'] and results['metadatas'][0]:
                for metadata in results['metadatas'][0]:
                    # Deserialize complex metadata
                    applies_to = self._deserialize_list_metadata(metadata.get('applies_to_json', '[]'))
                    
                    rule = BusinessRule(
                        rule_id=metadata['rule_id'],
                        description=metadata['description'],
                        applies_to=applies_to,
                        priority=metadata.get('priority', 'medium')
                    )
                    rules.append(rule)
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Error searching rules: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collections"""
        try:
            stats = {
                'schemas': self.schema_collection.count(),
                'examples': self.examples_collection.count(),
                'rules': self.rules_collection.count()
            }
            return stats
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return {'schemas': 0, 'examples': 0, 'rules': 0}
    
    def clear_all_collections(self):
        """Clear all collections"""
        try:
            self.client.delete_collection("schemas")
            self.client.delete_collection("examples")
            self.client.delete_collection("rules")
            self._initialize_collections()
            self.logger.info("All collections cleared and reinitialized")
        except Exception as e:
            self.logger.error(f"Error clearing collections: {str(e)}")


class ContextRetrieverFixed:
    """Fixed context retriever with proper metadata handling"""
    
    def __init__(self, vector_store: VectorStoreFixed):
        """
        Initialize context retriever
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
    
    def retrieve_context(self, 
                        question: str, 
                        intent: str = "general",
                        entities: List[str] = None) -> RetrievedContext:
        """
        Retrieve relevant context for a question
        
        Args:
            question: User question
            intent: Question intent
            entities: Extracted entities
            
        Returns:
            RetrievedContext with relevant information
        """
        try:
            # Build search query
            search_terms = [question]
            if entities:
                search_terms.extend(entities)
            search_query = " ".join(search_terms)
            
            # Search for relevant schemas
            schemas = self.vector_store.search_schemas(search_query, limit=5)
            
            # Search for relevant examples
            examples = self.vector_store.search_examples(search_query, limit=3)
            
            # Search for relevant rules
            rules = self.vector_store.search_rules(search_query, limit=5)
            
            # Create context
            context = RetrievedContext(
                schemas=schemas,
                examples=examples,
                rules=rules,
                metadata={
                    'search_query': search_query,
                    'intent': intent,
                    'entities': entities or [],
                    'schema_count': len(schemas),
                    'example_count': len(examples),
                    'rule_count': len(rules)
                }
            )
            
            self.logger.debug(f"Retrieved context: {len(schemas)} schemas, {len(examples)} examples, {len(rules)} rules")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            return RetrievedContext(
                schemas=[],
                examples=[],
                rules=[],
                metadata={'error': str(e)}
            )


class SchemaLoaderFixed:
    """Fixed schema loader with proper metadata handling"""
    
    def __init__(self, vector_store: VectorStoreFixed):
        """
        Initialize schema loader
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
    
    def load_retail_schemas(self):
        """Load retail database schemas"""
        schemas = [
            TableSchema(
                table_name="products",
                description="Product catalog with UPC codes, names, categories, and pricing information",
                columns=[
                    {"name": "upc_code", "type": "TEXT", "description": "Unique product identifier"},
                    {"name": "product_name", "type": "TEXT", "description": "Product name"},
                    {"name": "brand", "type": "TEXT", "description": "Brand name"},
                    {"name": "category_level_1", "type": "TEXT", "description": "Top-level category"},
                    {"name": "category_level_2", "type": "TEXT", "description": "Sub-category"},
                    {"name": "category_level_3", "type": "TEXT", "description": "Detailed category"},
                    {"name": "package_size", "type": "TEXT", "description": "Package size"},
                    {"name": "unit_of_measure", "type": "TEXT", "description": "Unit of measure"},
                    {"name": "cost", "type": "REAL", "description": "Product cost"},
                    {"name": "base_price", "type": "REAL", "description": "Base selling price"},
                    {"name": "price_family", "type": "TEXT", "description": "Price family group"}
                ]
            ),
            TableSchema(
                table_name="pricing",
                description="Current and historical pricing data with strategies and recommendations",
                columns=[
                    {"name": "upc_code", "type": "TEXT", "description": "Product identifier"},
                    {"name": "store_id", "type": "TEXT", "description": "Store identifier"},
                    {"name": "price_date", "type": "DATE", "description": "Price effective date"},
                    {"name": "current_price", "type": "REAL", "description": "Current selling price"},
                    {"name": "suggested_price", "type": "REAL", "description": "AI-recommended price"},
                    {"name": "price_family", "type": "TEXT", "description": "Price family group"},
                    {"name": "pricing_strategy", "type": "TEXT", "description": "Pricing strategy used"},
                    {"name": "price_change_reason", "type": "TEXT", "description": "Reason for price change"},
                    {"name": "units_impact", "type": "REAL", "description": "Projected units impact"},
                    {"name": "revenue_impact", "type": "REAL", "description": "Projected revenue impact"}
                ]
            ),
            TableSchema(
                table_name="elasticity",
                description="Price elasticity analysis for demand forecasting",
                columns=[
                    {"name": "upc_code", "type": "TEXT", "description": "Product identifier"},
                    {"name": "category_level_2", "type": "TEXT", "description": "Product category"},
                    {"name": "elasticity_value", "type": "REAL", "description": "Price elasticity coefficient"},
                    {"name": "elasticity_category", "type": "TEXT", "description": "Elasticity classification"},
                    {"name": "confidence_level", "type": "REAL", "description": "Elasticity confidence (0-1)"},
                    {"name": "last_updated", "type": "DATE", "description": "Last calculation date"}
                ]
            ),
            TableSchema(
                table_name="competitive_pricing",
                description="Competitive price monitoring and analysis",
                columns=[
                    {"name": "upc_code", "type": "TEXT", "description": "Product identifier"},
                    {"name": "competitor_name", "type": "TEXT", "description": "Competitor name"},
                    {"name": "competitor_price", "type": "REAL", "description": "Competitor's price"},
                    {"name": "our_price", "type": "REAL", "description": "Our current price"},
                    {"name": "cpi_value", "type": "REAL", "description": "Competitive Price Index"},
                    {"name": "price_gap", "type": "REAL", "description": "Price difference vs competitor"},
                    {"name": "price_gap_percent", "type": "REAL", "description": "Price gap percentage"},
                    {"name": "observation_date", "type": "DATE", "description": "Price observation date"}
                ]
            ),
            TableSchema(
                table_name="sales_data",
                description="Sales performance and forecasting data",
                columns=[
                    {"name": "upc_code", "type": "TEXT", "description": "Product identifier"},
                    {"name": "store_id", "type": "TEXT", "description": "Store identifier"},
                    {"name": "week_ending_date", "type": "DATE", "description": "Week ending date"},
                    {"name": "units_sold", "type": "INTEGER", "description": "Units sold"},
                    {"name": "revenue", "type": "REAL", "description": "Total revenue"},
                    {"name": "forecast_units", "type": "INTEGER", "description": "Forecasted units"},
                    {"name": "forecast_revenue", "type": "REAL", "description": "Forecasted revenue"}
                ]
            ),
            TableSchema(
                table_name="margin_analysis",
                description="Profit margin analysis and optimization",
                columns=[
                    {"name": "upc_code", "type": "TEXT", "description": "Product identifier"},
                    {"name": "store_id", "type": "TEXT", "description": "Store identifier"},
                    {"name": "analysis_date", "type": "DATE", "description": "Analysis date"},
                    {"name": "cost", "type": "REAL", "description": "Product cost"},
                    {"name": "selling_price", "type": "REAL", "description": "Selling price"},
                    {"name": "margin_amount", "type": "REAL", "description": "Margin amount"},
                    {"name": "margin_percent", "type": "REAL", "description": "Margin percentage"},
                    {"name": "margin_category", "type": "TEXT", "description": "Margin classification"}
                ]
            ),
            TableSchema(
                table_name="stores",
                description="Store information and geographic data",
                columns=[
                    {"name": "store_id", "type": "TEXT", "description": "Store identifier"},
                    {"name": "store_name", "type": "TEXT", "description": "Store name"},
                    {"name": "zone", "type": "TEXT", "description": "Geographic zone"},
                    {"name": "banner", "type": "TEXT", "description": "Store banner"},
                    {"name": "region", "type": "TEXT", "description": "Geographic region"},
                    {"name": "store_type", "type": "TEXT", "description": "Store type"},
                    {"name": "opened_date", "type": "DATE", "description": "Store opening date"}
                ]
            )
        ]
        
        # Add schemas to vector store
        for schema in schemas:
            self.vector_store.add_table_schema(schema)
        
        self.logger.info(f"Loaded {len(schemas)} retail schemas")
    
    def load_sample_examples(self):
        """Load sample query examples"""
        examples = [
            QueryExample(
                question="What is the current price for UPC code '0020282000000'?",
                sql_query="SELECT p.product_name, pr.current_price FROM products p JOIN pricing pr ON p.upc_code = pr.upc_code WHERE p.upc_code = '0020282000000' ORDER BY pr.price_date DESC LIMIT 1",
                description="Get current price for a specific product by UPC code",
                tables_used=["products", "pricing"],
                difficulty="easy"
            ),
            QueryExample(
                question="Show me the top 10 items by elasticity in the frozen food category",
                sql_query="SELECT p.product_name, e.elasticity_value FROM products p JOIN elasticity e ON p.upc_code = e.upc_code WHERE p.category_level_2 = 'FROZEN FOOD' ORDER BY e.elasticity_value DESC LIMIT 10",
                description="Find products with highest price elasticity in a specific category",
                tables_used=["products", "elasticity"],
                difficulty="medium"
            ),
            QueryExample(
                question="Which items have a CPI value higher than 1.05?",
                sql_query="SELECT DISTINCT p.product_name, cp.competitor_name, cp.cpi_value FROM products p JOIN competitive_pricing cp ON p.upc_code = cp.upc_code WHERE cp.cpi_value > 1.05 ORDER BY cp.cpi_value DESC",
                description="Find products where competitors have significantly higher prices",
                tables_used=["products", "competitive_pricing"],
                difficulty="medium"
            )
        ]
        
        # Add examples to vector store
        for example in examples:
            self.vector_store.add_query_example(example)
        
        self.logger.info(f"Loaded {len(examples)} sample examples")
    
    def load_business_rules(self):
        """Load business rules"""
        rules = [
            BusinessRule(
                rule_id="elasticity_pricing",
                description="Products with high elasticity (>1.5) should be considered for price reductions to drive volume",
                applies_to=["elasticity", "pricing"],
                priority="high"
            ),
            BusinessRule(
                rule_id="competitive_positioning",
                description="Maintain competitive pricing within 5% of key competitors unless justified by value proposition",
                applies_to=["competitive_pricing", "pricing"],
                priority="high"
            ),
            BusinessRule(
                rule_id="margin_optimization",
                description="Target minimum 20% margin on non-promotional items while considering elasticity impact",
                applies_to=["pricing", "sales_data", "elasticity"],
                priority="medium"
            )
        ]
        
        # Add rules to vector store
        for rule in rules:
            self.vector_store.add_business_rule(rule)
        
        self.logger.info(f"Loaded {len(rules)} business rules")


# Factory function for easy creation
def create_fixed_vector_store(persist_directory: str = "./chroma_db") -> VectorStoreFixed:
    """
    Factory function to create a fixed vector store
    
    Args:
        persist_directory: Directory to persist the vector database
        
    Returns:
        VectorStoreFixed instance
    """
    return VectorStoreFixed(persist_directory)


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create fixed vector store
    vector_store = create_fixed_vector_store("./test_chroma_db")
    
    # Create schema loader
    schema_loader = SchemaLoaderFixed(vector_store)
    
    # Load data
    print("Loading retail schemas...")
    schema_loader.load_retail_schemas()
    
    print("Loading sample examples...")
    schema_loader.load_sample_examples()
    
    print("Loading business rules...")
    schema_loader.load_business_rules()
    
    # Test retrieval
    context_retriever = ContextRetrieverFixed(vector_store)
    
    print("\nTesting context retrieval...")
    context = context_retriever.retrieve_context(
        "What is the current price for UPC code 123456?",
        intent="pricing",
        entities=["UPC", "price"]
    )
    
    print(f"Retrieved {len(context.schemas)} schemas, {len(context.examples)} examples, {len(context.rules)} rules")
    
    # Get stats
    stats = vector_store.get_collection_stats()
    print(f"\nCollection stats: {stats}")
    
    print("Fixed vector store test completed!")

