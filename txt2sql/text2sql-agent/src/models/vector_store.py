"""
Vector Store and Context Retrieval System for Text-to-SQL Agent

This module handles the storage and retrieval of database schema information,
metadata, and similar query examples using vector embeddings for semantic search.
"""

import os
import json
import logging
import pickle
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
import numpy as np
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import hashlib


@dataclass
class SchemaInfo:
    """Database schema information"""
    table_name: str
    columns: List[Dict[str, str]]
    description: str
    relationships: List[Dict[str, str]]
    sample_queries: List[str]
    business_context: str
    data_types: Dict[str, str]
    constraints: List[str]


@dataclass
class QueryExample:
    """Example query with natural language question"""
    question: str
    sql_query: str
    explanation: str
    tables_used: List[str]
    query_type: str
    complexity: float
    success_rate: float


@dataclass
class BusinessRule:
    """Business rule or domain knowledge"""
    rule_id: str
    title: str
    description: str
    applies_to: List[str]  # Tables or domains this rule applies to
    examples: List[str]
    priority: int


@dataclass
class ContextResult:
    """Result of context retrieval"""
    schemas: List[SchemaInfo]
    examples: List[QueryExample]
    rules: List[BusinessRule]
    metadata: Dict[str, Any]
    similarity_scores: List[float]


class EmbeddingManager:
    """Manages embeddings using OpenAI's embedding model"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = "text-embedding-3-small"  # More cost-effective for this use case
        self.logger = logging.getLogger(__name__)
        
        # Cache for embeddings to avoid redundant API calls
        self.embedding_cache = {}
        self.cache_file = "embedding_cache.pkl"
        self._load_cache()
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text with caching"""
        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            self.embedding_cache[cache_key] = embedding
            self._save_cache()
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error getting embedding: {str(e)}")
            return [0.0] * 1536  # Return zero vector as fallback
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts efficiently"""
        # Check cache first
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in self.embedding_cache:
                embeddings.append(self.embedding_cache[cache_key])
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Get embeddings for uncached texts
        if uncached_texts:
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=uncached_texts
                )
                
                for i, embedding_data in enumerate(response.data):
                    embedding = embedding_data.embedding
                    original_index = uncached_indices[i]
                    embeddings[original_index] = embedding
                    
                    # Cache the result
                    cache_key = hashlib.md5(uncached_texts[i].encode()).hexdigest()
                    self.embedding_cache[cache_key] = embedding
                
                self._save_cache()
                
            except Exception as e:
                self.logger.error(f"Error getting batch embeddings: {str(e)}")
                # Fill with zero vectors
                for i in uncached_indices:
                    embeddings[i] = [0.0] * 1536
        
        return embeddings
    
    def _load_cache(self):
        """Load embedding cache from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load embedding cache: {str(e)}")
            self.embedding_cache = {}
    
    def _save_cache(self):
        """Save embedding cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
        except Exception as e:
            self.logger.warning(f"Could not save embedding cache: {str(e)}")


class VectorStore:
    """Vector store for schema, examples, and business rules"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embedding_manager = EmbeddingManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create collections
        self.schema_collection = self._get_or_create_collection("schemas")
        self.examples_collection = self._get_or_create_collection("examples")
        self.rules_collection = self._get_or_create_collection("rules")
        
        self.logger.info(f"Vector store initialized with {persist_directory}")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name)
        except:
            return self.client.create_collection(
                name=name,
                embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.getenv('OPENAI_API_KEY'),
                    model_name="text-embedding-3-small"
                )
            )
    
    def add_schema(self, schema: SchemaInfo):
        """Add schema information to the vector store"""
        try:
            # Create searchable text from schema
            schema_text = self._schema_to_text(schema)
            
            # Add to collection
            self.schema_collection.add(
                documents=[schema_text],
                metadatas=[asdict(schema)],
                ids=[f"schema_{schema.table_name}"]
            )
            
            self.logger.info(f"Added schema for table: {schema.table_name}")
            
        except Exception as e:
            self.logger.error(f"Error adding schema: {str(e)}")
    
    def add_example(self, example: QueryExample):
        """Add query example to the vector store"""
        try:
            # Create searchable text from example
            example_text = f"{example.question} {example.explanation}"
            
            # Generate unique ID
            example_id = hashlib.md5(example.question.encode()).hexdigest()
            
            # Add to collection
            self.examples_collection.add(
                documents=[example_text],
                metadatas=[asdict(example)],
                ids=[f"example_{example_id}"]
            )
            
            self.logger.info(f"Added query example: {example.question[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error adding example: {str(e)}")
    
    def add_business_rule(self, rule: BusinessRule):
        """Add business rule to the vector store"""
        try:
            # Create searchable text from rule
            rule_text = f"{rule.title} {rule.description} {' '.join(rule.examples)}"
            
            # Add to collection
            self.rules_collection.add(
                documents=[rule_text],
                metadatas=[asdict(rule)],
                ids=[f"rule_{rule.rule_id}"]
            )
            
            self.logger.info(f"Added business rule: {rule.title}")
            
        except Exception as e:
            self.logger.error(f"Error adding business rule: {str(e)}")
    
    def search_schemas(self, query: str, n_results: int = 5) -> List[SchemaInfo]:
        """Search for relevant schemas"""
        try:
            results = self.schema_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            schemas = []
            for metadata in results['metadatas'][0]:
                schema = SchemaInfo(**metadata)
                schemas.append(schema)
            
            return schemas
            
        except Exception as e:
            self.logger.error(f"Error searching schemas: {str(e)}")
            return []
    
    def search_examples(self, query: str, n_results: int = 3) -> List[QueryExample]:
        """Search for similar query examples"""
        try:
            results = self.examples_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            examples = []
            for metadata in results['metadatas'][0]:
                example = QueryExample(**metadata)
                examples.append(example)
            
            return examples
            
        except Exception as e:
            self.logger.error(f"Error searching examples: {str(e)}")
            return []
    
    def search_business_rules(self, query: str, n_results: int = 5) -> List[BusinessRule]:
        """Search for relevant business rules"""
        try:
            results = self.rules_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            rules = []
            for metadata in results['metadatas'][0]:
                rule = BusinessRule(**metadata)
                rules.append(rule)
            
            return rules
            
        except Exception as e:
            self.logger.error(f"Error searching business rules: {str(e)}")
            return []
    
    def _schema_to_text(self, schema: SchemaInfo) -> str:
        """Convert schema to searchable text"""
        text_parts = [
            f"Table: {schema.table_name}",
            f"Description: {schema.description}",
            f"Business Context: {schema.business_context}"
        ]
        
        # Add column information
        for col in schema.columns:
            col_text = f"Column {col['name']} ({col['type']})"
            if col.get('description'):
                col_text += f": {col['description']}"
            text_parts.append(col_text)
        
        # Add relationships
        for rel in schema.relationships:
            text_parts.append(f"Relationship: {rel}")
        
        return " ".join(text_parts)
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about the collections"""
        return {
            'schemas': self.schema_collection.count(),
            'examples': self.examples_collection.count(),
            'rules': self.rules_collection.count()
        }


class ContextRetriever:
    """Main context retrieval system"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
    
    def retrieve_context(self, question: str, intent: str = None, 
                        entities: List[str] = None) -> ContextResult:
        """
        Retrieve relevant context for a question
        
        Args:
            question: Natural language question
            intent: Classified intent (optional)
            entities: Extracted entities (optional)
            
        Returns:
            ContextResult with relevant information
        """
        try:
            # Build enhanced query for better retrieval
            enhanced_query = self._build_enhanced_query(question, intent, entities)
            
            # Search for relevant schemas
            schemas = self.vector_store.search_schemas(enhanced_query, n_results=5)
            
            # Search for similar examples
            examples = self.vector_store.search_examples(enhanced_query, n_results=3)
            
            # Search for business rules
            rules = self.vector_store.search_business_rules(enhanced_query, n_results=5)
            
            # Calculate relevance scores (simplified)
            similarity_scores = [0.9] * len(schemas)  # Placeholder
            
            # Build metadata
            metadata = {
                'query': question,
                'enhanced_query': enhanced_query,
                'intent': intent,
                'entities': entities or [],
                'retrieval_timestamp': str(np.datetime64('now'))
            }
            
            return ContextResult(
                schemas=schemas,
                examples=examples,
                rules=rules,
                metadata=metadata,
                similarity_scores=similarity_scores
            )
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            return ContextResult(
                schemas=[],
                examples=[],
                rules=[],
                metadata={'error': str(e)},
                similarity_scores=[]
            )
    
    def _build_enhanced_query(self, question: str, intent: str = None, 
                            entities: List[str] = None) -> str:
        """Build enhanced query for better retrieval"""
        query_parts = [question]
        
        if intent:
            query_parts.append(f"intent:{intent}")
        
        if entities:
            query_parts.extend(entities)
        
        return " ".join(query_parts)


class SchemaLoader:
    """Loads and manages database schema information"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
    
    def load_retail_schemas(self):
        """Load predefined retail analytics schemas"""
        schemas = [
            SchemaInfo(
                table_name="products",
                columns=[
                    {"name": "upc_code", "type": "STRING", "description": "Unique product identifier"},
                    {"name": "product_name", "type": "STRING", "description": "Product description"},
                    {"name": "category", "type": "STRING", "description": "Product category"},
                    {"name": "subcategory", "type": "STRING", "description": "Product subcategory"},
                    {"name": "brand", "type": "STRING", "description": "Product brand"},
                    {"name": "price_family", "type": "STRING", "description": "Price family grouping"},
                    {"name": "product_group", "type": "STRING", "description": "Product group classification"},
                    {"name": "kvi_group", "type": "STRING", "description": "Key Value Item group"},
                    {"name": "level_2", "type": "STRING", "description": "Level 2 category hierarchy"}
                ],
                description="Master product catalog with hierarchical categorization",
                relationships=[
                    {"type": "one_to_many", "table": "pricing", "key": "upc_code"},
                    {"type": "one_to_many", "table": "elasticity", "key": "upc_code"}
                ],
                sample_queries=[
                    "SELECT * FROM products WHERE upc_code = '0020282000000'",
                    "SELECT * FROM products WHERE category = 'FROZEN FOOD'"
                ],
                business_context="Central product master containing all product information and hierarchical classifications",
                data_types={"upc_code": "STRING", "price_family": "STRING"},
                constraints=["upc_code is unique", "category cannot be null"]
            ),
            
            SchemaInfo(
                table_name="pricing",
                columns=[
                    {"name": "upc_code", "type": "STRING", "description": "Product identifier"},
                    {"name": "zone", "type": "STRING", "description": "Geographic or business zone"},
                    {"name": "current_price", "type": "FLOAT", "description": "Current retail price"},
                    {"name": "suggested_price", "type": "FLOAT", "description": "AI-recommended price"},
                    {"name": "cp_unit_price", "type": "FLOAT", "description": "Competitor unit price"},
                    {"name": "week_ending", "type": "DATE", "description": "Week ending date"},
                    {"name": "price_change_amount", "type": "FLOAT", "description": "Price change amount"},
                    {"name": "margin_percent", "type": "FLOAT", "description": "Profit margin percentage"},
                    {"name": "cost", "type": "FLOAT", "description": "Product cost"},
                    {"name": "exported", "type": "BOOLEAN", "description": "Whether price was exported"}
                ],
                description="Current and suggested pricing information by zone and time",
                relationships=[
                    {"type": "many_to_one", "table": "products", "key": "upc_code"},
                    {"type": "one_to_many", "table": "price_changes", "key": "upc_code"}
                ],
                sample_queries=[
                    "SELECT current_price, suggested_price FROM pricing WHERE upc_code = '0020282000000' AND zone = 'Banner 2'",
                    "SELECT * FROM pricing WHERE week_ending = '2025-04-15'"
                ],
                business_context="Pricing data with current and recommended prices across different zones",
                data_types={"current_price": "FLOAT", "suggested_price": "FLOAT"},
                constraints=["current_price > 0", "zone cannot be null"]
            ),
            
            SchemaInfo(
                table_name="elasticity",
                columns=[
                    {"name": "upc_code", "type": "STRING", "description": "Product identifier"},
                    {"name": "zone", "type": "STRING", "description": "Geographic zone"},
                    {"name": "elasticity_value", "type": "FLOAT", "description": "Price elasticity coefficient"},
                    {"name": "confidence_score", "type": "FLOAT", "description": "Elasticity confidence (0-1)"},
                    {"name": "units_impact", "type": "FLOAT", "description": "Projected units impact"},
                    {"name": "revenue_impact", "type": "FLOAT", "description": "Projected revenue impact"},
                    {"name": "profit_impact", "type": "FLOAT", "description": "Projected profit impact"},
                    {"name": "calculation_date", "type": "DATE", "description": "When elasticity was calculated"}
                ],
                description="Price elasticity measurements and demand sensitivity analysis",
                relationships=[
                    {"type": "many_to_one", "table": "products", "key": "upc_code"}
                ],
                sample_queries=[
                    "SELECT elasticity_value FROM elasticity WHERE upc_code = '0020282000000'",
                    "SELECT * FROM elasticity WHERE elasticity_value > 1.5"
                ],
                business_context="Price elasticity data showing demand sensitivity to price changes",
                data_types={"elasticity_value": "FLOAT", "confidence_score": "FLOAT"},
                constraints=["confidence_score BETWEEN 0 AND 1"]
            ),
            
            SchemaInfo(
                table_name="sales",
                columns=[
                    {"name": "upc_code", "type": "STRING", "description": "Product identifier"},
                    {"name": "zone", "type": "STRING", "description": "Geographic zone"},
                    {"name": "week_ending", "type": "DATE", "description": "Week ending date"},
                    {"name": "units_sold", "type": "INTEGER", "description": "Units sold"},
                    {"name": "revenue", "type": "FLOAT", "description": "Total revenue"},
                    {"name": "profit", "type": "FLOAT", "description": "Total profit"},
                    {"name": "forecast_units", "type": "INTEGER", "description": "Forecasted units"},
                    {"name": "forecast_revenue", "type": "FLOAT", "description": "Forecasted revenue"}
                ],
                description="Historical and forecasted sales performance data",
                relationships=[
                    {"type": "many_to_one", "table": "products", "key": "upc_code"}
                ],
                sample_queries=[
                    "SELECT SUM(revenue) FROM sales WHERE week_ending >= '2025-04-01'",
                    "SELECT * FROM sales WHERE upc_code = '0020282000000' ORDER BY week_ending DESC"
                ],
                business_context="Sales performance tracking with historical and forecasted data",
                data_types={"units_sold": "INTEGER", "revenue": "FLOAT"},
                constraints=["units_sold >= 0", "revenue >= 0"]
            ),
            
            SchemaInfo(
                table_name="competitor_prices",
                columns=[
                    {"name": "upc_code", "type": "STRING", "description": "Product identifier"},
                    {"name": "competitor_name", "type": "STRING", "description": "Competitor name"},
                    {"name": "competitor_price", "type": "FLOAT", "description": "Competitor's price"},
                    {"name": "price_date", "type": "DATE", "description": "Price observation date"},
                    {"name": "cpi_value", "type": "FLOAT", "description": "Competitive Price Index"},
                    {"name": "price_gap", "type": "FLOAT", "description": "Price difference vs competitor"}
                ],
                description="Competitor pricing intelligence and market positioning data",
                relationships=[
                    {"type": "many_to_one", "table": "products", "key": "upc_code"}
                ],
                sample_queries=[
                    "SELECT competitor_price FROM competitor_prices WHERE upc_code = '0020282000000' AND competitor_name = 'Walmart'",
                    "SELECT * FROM competitor_prices WHERE cpi_value > 1.05"
                ],
                business_context="Competitive pricing data for market positioning analysis",
                data_types={"competitor_price": "FLOAT", "cpi_value": "FLOAT"},
                constraints=["competitor_price > 0", "cpi_value > 0"]
            )
        ]
        
        # Add schemas to vector store
        for schema in schemas:
            self.vector_store.add_schema(schema)
        
        self.logger.info(f"Loaded {len(schemas)} retail schemas")
    
    def load_sample_examples(self):
        """Load sample query examples"""
        examples = [
            QueryExample(
                question="What is the current price for UPC code '0020282000000'?",
                sql_query="SELECT current_price FROM pricing WHERE upc_code = '0020282000000' AND week_ending = (SELECT MAX(week_ending) FROM pricing WHERE upc_code = '0020282000000')",
                explanation="Retrieves the most recent current price for the specified UPC code",
                tables_used=["pricing"],
                query_type="price_lookup",
                complexity=0.3,
                success_rate=0.95
            ),
            
            QueryExample(
                question="Show me the top 10 items by elasticity in the frozen food category",
                sql_query="SELECT p.upc_code, p.product_name, e.elasticity_value FROM products p JOIN elasticity e ON p.upc_code = e.upc_code WHERE p.category = 'FROZEN FOOD' ORDER BY e.elasticity_value DESC LIMIT 10",
                explanation="Joins products and elasticity tables to find highest elasticity items in frozen food",
                tables_used=["products", "elasticity"],
                query_type="elasticity_analysis",
                complexity=0.6,
                success_rate=0.88
            ),
            
            QueryExample(
                question="What are the pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'?",
                sql_query="SELECT p.upc_code, p.product_name, pr.current_price, pr.suggested_price, pr.price_change_amount FROM products p JOIN pricing pr ON p.upc_code = pr.upc_code WHERE p.level_2 = 'BREAD & WRAPS' AND pr.zone = 'Banner 2' AND pr.week_ending = (SELECT MAX(week_ending) FROM pricing)",
                explanation="Retrieves current pricing strategy for products in specific category and zone",
                tables_used=["products", "pricing"],
                query_type="price_analysis",
                complexity=0.7,
                success_rate=0.82
            )
        ]
        
        # Add examples to vector store
        for example in examples:
            self.vector_store.add_example(example)
        
        self.logger.info(f"Loaded {len(examples)} sample examples")
    
    def load_business_rules(self):
        """Load business rules and domain knowledge"""
        rules = [
            BusinessRule(
                rule_id="elasticity_interpretation",
                title="Price Elasticity Interpretation",
                description="Elasticity > 1 means elastic (price sensitive), < 1 means inelastic (price insensitive)",
                applies_to=["elasticity", "pricing"],
                examples=[
                    "Elasticity of 1.5 means 1% price increase leads to 1.5% demand decrease",
                    "Elasticity of 0.8 means demand is relatively insensitive to price changes"
                ],
                priority=1
            ),
            
            BusinessRule(
                rule_id="cpi_calculation",
                title="Competitive Price Index (CPI)",
                description="CPI = Our Price / Competitor Average Price. CPI > 1 means we're more expensive",
                applies_to=["competitor_prices", "pricing"],
                examples=[
                    "CPI of 1.05 means we're 5% more expensive than competitors",
                    "CPI of 0.95 means we're 5% cheaper than competitors"
                ],
                priority=1
            ),
            
            BusinessRule(
                rule_id="date_filtering",
                title="Date Filtering Best Practices",
                description="Always use the most recent data unless historical analysis is specifically requested",
                applies_to=["pricing", "sales", "elasticity"],
                examples=[
                    "Use MAX(week_ending) for current prices",
                    "Filter by specific date ranges for trend analysis"
                ],
                priority=2
            )
        ]
        
        # Add rules to vector store
        for rule in rules:
            self.vector_store.add_business_rule(rule)
        
        self.logger.info(f"Loaded {len(rules)} business rules")


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize vector store
    vector_store = VectorStore("./test_chroma_db")
    
    # Load schemas and examples
    loader = SchemaLoader(vector_store)
    loader.load_retail_schemas()
    loader.load_sample_examples()
    loader.load_business_rules()
    
    # Test context retrieval
    retriever = ContextRetriever(vector_store)
    
    test_question = "What is the current price for UPC code '0020282000000'?"
    context = retriever.retrieve_context(test_question, intent="price_lookup")
    
    print(f"Retrieved {len(context.schemas)} schemas")
    print(f"Retrieved {len(context.examples)} examples")
    print(f"Retrieved {len(context.rules)} rules")
    
    # Print collection stats
    stats = vector_store.get_collection_stats()
    print(f"Collection stats: {stats}")

