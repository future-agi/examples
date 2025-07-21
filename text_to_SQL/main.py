import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time
import pandas as pd
import sqlite3
import os
import json

from langchain.sql_database import SQLDatabase
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import Tool
from sqlalchemy import create_engine, text
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType, EvalName, EvalTag, EvalTagType, EvalSpanKind

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="FUTURE_AGI-OPENAI-AUDIO",
)

from traceai_langchain import LangChainInstrumentor

LangChainInstrumentor().instrument(tracer_provider=trace_provider)

# Complex database schema for e-commerce platform
COMPLEX_DB_SCHEMA = """
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    date_of_birth DATE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    account_type TEXT CHECK (account_type IN ('standard', 'premium', 'admin')) DEFAULT 'standard'
);

CREATE TABLE product_categories (
    category_id INTEGER PRIMARY KEY,
    parent_category_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (parent_category_id) REFERENCES product_categories(category_id) ON DELETE SET NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    inventory_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

CREATE TABLE product_category_mappings (
    product_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, category_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES product_categories(category_id) ON DELETE CASCADE
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_method TEXT NOT NULL,
    payment_status TEXT CHECK (payment_status IN ('pending', 'authorized', 'paid', 'refunded', 'failed')) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
);

CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title TEXT,
    content TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_votes INTEGER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

# Sample data for the complex schema (simplified for brevity)
COMPLEX_SAMPLE_DATA = {
    "users": [
        {"user_id": 1, "username": "johndoe", "email": "john@example.com", "password_hash": "hash1", "first_name": "John", "last_name": "Doe", "date_of_birth": "1985-05-15", "registration_date": "2022-01-10", "last_login": "2023-05-01", "is_active": 1, "account_type": "premium"},
        {"user_id": 2, "username": "janedoe", "email": "jane@example.com", "password_hash": "hash2", "first_name": "Jane", "last_name": "Doe", "date_of_birth": "1990-08-20", "registration_date": "2022-02-15", "last_login": "2023-05-02", "is_active": 1, "account_type": "standard"},
        {"user_id": 3, "username": "bobsmith", "email": "bob@example.com", "password_hash": "hash3", "first_name": "Bob", "last_name": "Smith", "date_of_birth": "1978-11-30", "registration_date": "2022-03-20", "last_login": "2023-04-28", "is_active": 1, "account_type": "standard"},
        {"user_id": 4, "username": "alicejones", "email": "alice@example.com", "password_hash": "hash4", "first_name": "Alice", "last_name": "Jones", "date_of_birth": "1992-02-25", "registration_date": "2022-04-05", "last_login": "2023-05-03", "is_active": 1, "account_type": "premium"},
        {"user_id": 5, "username": "adminuser", "email": "admin@example.com", "password_hash": "hash5", "first_name": "Admin", "last_name": "User", "date_of_birth": "1980-01-01", "registration_date": "2022-01-01", "last_login": "2023-05-04", "is_active": 1, "account_type": "admin"}
    ],
    "product_categories": [
        {"category_id": 1, "parent_category_id": None, "name": "Electronics", "description": "Electronic devices and accessories", "display_order": 1},
        {"category_id": 2, "parent_category_id": 1, "name": "Smartphones", "description": "Mobile phones and accessories", "display_order": 1},
        {"category_id": 3, "parent_category_id": 1, "name": "Laptops", "description": "Portable computers", "display_order": 2},
        {"category_id": 4, "parent_category_id": None, "name": "Clothing", "description": "Apparel and fashion items", "display_order": 2},
        {"category_id": 5, "parent_category_id": 4, "name": "Men's Clothing", "description": "Clothing for men", "display_order": 1},
        {"category_id": 6, "parent_category_id": 4, "name": "Women's Clothing", "description": "Clothing for women", "display_order": 2}
    ],
    "products": [
        {"product_id": 1, "sku": "PHONE001", "name": "Smartphone X", "description": "Latest smartphone with advanced features", "price": 999.99, "cost": 700.00, "inventory_count": 50, "is_active": 1, "date_added": "2022-01-15", "last_updated": "2023-04-01"},
        {"product_id": 2, "sku": "PHONE002", "name": "Smartphone Y", "description": "Mid-range smartphone with good camera", "price": 599.99, "cost": 400.00, "inventory_count": 75, "is_active": 1, "date_added": "2022-02-10", "last_updated": "2023-03-15"},
        {"product_id": 3, "sku": "LAPTOP001", "name": "Laptop Pro", "description": "High-performance laptop for professionals", "price": 1499.99, "cost": 1100.00, "inventory_count": 30, "is_active": 1, "date_added": "2022-01-20", "last_updated": "2023-02-10"},
        {"product_id": 4, "sku": "TSHIRT001", "name": "Men's T-Shirt", "description": "Comfortable cotton t-shirt", "price": 24.99, "cost": 10.00, "inventory_count": 200, "is_active": 1, "date_added": "2022-03-01", "last_updated": "2023-01-15"},
        {"product_id": 5, "sku": "DRESS001", "name": "Women's Summer Dress", "description": "Lightweight summer dress", "price": 49.99, "cost": 20.00, "inventory_count": 100, "is_active": 1, "date_added": "2022-03-15", "last_updated": "2023-02-20"}
    ],
    "product_category_mappings": [
        {"product_id": 1, "category_id": 2},
        {"product_id": 2, "category_id": 2},
        {"product_id": 3, "category_id": 3},
        {"product_id": 4, "category_id": 5},
        {"product_id": 5, "category_id": 6}
    ],
    "orders": [
        {"order_id": 1, "user_id": 1, "order_date": "2023-01-15", "status": "delivered", "total_amount": 1085.98, "payment_method": "Credit Card", "payment_status": "paid"},
        {"order_id": 2, "user_id": 2, "order_date": "2023-02-20", "status": "shipped", "total_amount": 653.98, "payment_method": "PayPal", "payment_status": "paid"},
        {"order_id": 3, "user_id": 3, "order_date": "2023-03-10", "status": "processing", "total_amount": 1625.98, "payment_method": "Credit Card", "payment_status": "paid"},
        {"order_id": 4, "user_id": 4, "order_date": "2023-04-05", "status": "delivered", "total_amount": 29.98, "payment_method": "Credit Card", "payment_status": "paid"},
        {"order_id": 5, "user_id": 1, "order_date": "2023-04-20", "status": "pending", "total_amount": 655.98, "payment_method": "Credit Card", "payment_status": "pending"}
    ],
    "order_items": [
        {"order_item_id": 1, "order_id": 1, "product_id": 1, "quantity": 1, "unit_price": 999.99, "total_price": 999.99},
        {"order_item_id": 2, "order_id": 2, "product_id": 2, "quantity": 1, "unit_price": 599.99, "total_price": 599.99},
        {"order_item_id": 3, "order_id": 3, "product_id": 3, "quantity": 1, "unit_price": 1499.99, "total_price": 1499.99},
        {"order_item_id": 4, "order_id": 4, "product_id": 4, "quantity": 1, "unit_price": 24.99, "total_price": 24.99},
        {"order_item_id": 5, "order_id": 5, "product_id": 2, "quantity": 1, "unit_price": 599.99, "total_price": 599.99}
    ],
    "reviews": [
        {"review_id": 1, "product_id": 1, "user_id": 2, "rating": 5, "title": "Great phone!", "content": "This is the best smartphone I've ever owned.", "review_date": "2023-02-01", "is_verified_purchase": 0, "helpful_votes": 10},
        {"review_id": 2, "product_id": 1, "user_id": 3, "rating": 4, "title": "Good but expensive", "content": "Great features but a bit pricey.", "review_date": "2023-02-15", "is_verified_purchase": 0, "helpful_votes": 5},
        {"review_id": 3, "product_id": 2, "user_id": 1, "rating": 4, "title": "Solid mid-range phone", "content": "Good value for the price.", "review_date": "2023-03-01", "is_verified_purchase": 1, "helpful_votes": 8},
        {"review_id": 4, "product_id": 3, "user_id": 4, "rating": 5, "title": "Perfect for work", "content": "Fast and reliable laptop for professional use.", "review_date": "2023-03-20", "is_verified_purchase": 1, "helpful_votes": 12},
        {"review_id": 5, "product_id": 4, "user_id": 2, "rating": 3, "title": "Decent quality", "content": "Comfortable but runs small.", "review_date": "2023-04-10", "is_verified_purchase": 1, "helpful_votes": 3}
    ]
}

# Complex SQL queries for testing LLM capabilities
COMPLEX_TEXT2SQL_GROUND_TRUTH = {
    "Find the top 3 products with the highest average rating that have at least 2 reviews": 
        """SELECT p.product_id, p.name, AVG(r.rating) as avg_rating, COUNT(r.review_id) as review_count 
        FROM products p 
        JOIN reviews r ON p.product_id = r.product_id 
        GROUP BY p.product_id 
        HAVING COUNT(r.review_id) >= 2 
        ORDER BY avg_rating DESC 
        LIMIT 3""",
    
    "Calculate the total revenue by product category for the last quarter, including only completed orders": 
        """SELECT pc.category_id, pc.name, SUM(oi.total_price) as total_revenue 
        FROM product_categories pc 
        JOIN product_category_mappings pcm ON pc.category_id = pcm.category_id 
        JOIN products p ON pcm.product_id = p.product_id 
        JOIN order_items oi ON p.product_id = oi.product_id 
        JOIN orders o ON oi.order_id = o.order_id 
        WHERE o.status IN ('delivered', 'shipped') 
        AND o.order_date >= date('now', '-3 month') 
        GROUP BY pc.category_id 
        ORDER BY total_revenue DESC""",
    
    "Find users who have purchased products from multiple categories": 
        """SELECT u.user_id, u.username, COUNT(DISTINCT pc.category_id) as category_count 
        FROM users u 
        JOIN orders o ON u.user_id = o.user_id 
        JOIN order_items oi ON o.order_id = oi.order_id 
        JOIN product_category_mappings pcm ON oi.product_id = pcm.product_id 
        JOIN product_categories pc ON pcm.category_id = pc.category_id 
        WHERE o.payment_status = 'paid' 
        GROUP BY u.user_id 
        HAVING category_count > 1 
        ORDER BY category_count DESC""",
    
    # "Identify the most popular products based on order quantity": 
    #     """SELECT p.product_id, p.name, SUM(oi.quantity) as total_quantity_ordered, 
    #     COUNT(DISTINCT o.order_id) as order_count 
    #     FROM products p 
    #     JOIN order_items oi ON p.product_id = oi.product_id 
    #     JOIN orders o ON oi.order_id = o.order_id 
    #     WHERE o.payment_status = 'paid' 
    #     GROUP BY p.product_id 
    #     ORDER BY total_quantity_ordered DESC 
    #     LIMIT 5""",
    
    # "Calculate the average rating for products in each category": 
    #     """SELECT pc.category_id, pc.name, AVG(r.rating) as avg_category_rating, 
    #     COUNT(r.review_id) as review_count 
    #     FROM product_categories pc 
    #     JOIN product_category_mappings pcm ON pc.category_id = pcm.category_id 
    #     JOIN products p ON pcm.product_id = p.product_id 
    #     LEFT JOIN reviews r ON p.product_id = r.product_id 
    #     GROUP BY pc.category_id 
    #     HAVING review_count > 0 
    #     ORDER BY avg_category_rating DESC""",
        
    # "Find products with higher than average price in their respective categories":
    #     """SELECT p.product_id, p.name, p.price, pc.name as category_name, avg_cat_price.avg_price
    #     FROM products p
    #     JOIN product_category_mappings pcm ON p.product_id = pcm.product_id
    #     JOIN product_categories pc ON pcm.category_id = pc.category_id
    #     JOIN (
    #         SELECT pcm.category_id, AVG(p.price) as avg_price
    #         FROM products p
    #         JOIN product_category_mappings pcm ON p.product_id = pcm.product_id
    #         GROUP BY pcm.category_id
    #     ) avg_cat_price ON pcm.category_id = avg_cat_price.category_id
    #     WHERE p.price > avg_cat_price.avg_price
    #     ORDER BY (p.price - avg_cat_price.avg_price) DESC""",
        
    # "Identify users who have left reviews for products they've purchased":
    #     """SELECT u.user_id, u.username, COUNT(r.review_id) as verified_review_count
    #     FROM users u
    #     JOIN reviews r ON u.user_id = r.user_id
    #     JOIN orders o ON u.user_id = o.user_id
    #     JOIN order_items oi ON o.order_id = oi.order_id AND oi.product_id = r.product_id
    #     WHERE r.is_verified_purchase = 1
    #     GROUP BY u.user_id
    #     ORDER BY verified_review_count DESC""",
        
    # "Calculate the profit margin for each product and rank them":
    #     """SELECT product_id, name, price, cost, 
    #     (price - cost) as profit_margin,
    #     ((price - cost) / cost * 100) as profit_percentage
    #     FROM products
    #     ORDER BY profit_percentage DESC""",
        
    # "Find the most recent order for each user along with their total spending":
    #     """SELECT u.user_id, u.username, MAX(o.order_date) as last_order_date,
    #     COUNT(DISTINCT o.order_id) as total_orders,
    #     SUM(o.total_amount) as total_spent
    #     FROM users u
    #     LEFT JOIN orders o ON u.user_id = o.user_id
    #     WHERE o.payment_status = 'paid'
    #     GROUP BY u.user_id
    #     ORDER BY total_spent DESC""",
        
    # "Identify product categories with no products or no orders in the last month":
    #     """SELECT pc.category_id, pc.name, 
    #     COUNT(DISTINCT p.product_id) as product_count,
    #     COUNT(DISTINCT oi.order_item_id) as recent_order_items
    #     FROM product_categories pc
    #     LEFT JOIN product_category_mappings pcm ON pc.category_id = pcm.category_id
    #     LEFT JOIN products p ON pcm.product_id = p.product_id
    #     LEFT JOIN order_items oi ON p.product_id = oi.product_id
    #     LEFT JOIN orders o ON oi.order_id = o.order_id AND o.order_date >= date('now', '-1 month')
    #     GROUP BY pc.category_id
    #     HAVING product_count = 0 OR recent_order_items = 0
    #     ORDER BY pc.name""",
        
    # "Find customers who have spent more than the average customer in the last 6 months":
    #     """SELECT u.user_id, u.username, SUM(o.total_amount) as total_spent,
    #     (SELECT AVG(total_spent) FROM (
    #         SELECT u2.user_id, SUM(o2.total_amount) as total_spent
    #         FROM users u2
    #         JOIN orders o2 ON u2.user_id = o2.user_id
    #         WHERE o2.order_date >= date('now', '-6 month')
    #         AND o2.payment_status = 'paid'
    #         GROUP BY u2.user_id
    #     )) as avg_customer_spend
    #     FROM users u
    #     JOIN orders o ON u.user_id = o.user_id
    #     WHERE o.order_date >= date('now', '-6 month')
    #     AND o.payment_status = 'paid'
    #     GROUP BY u.user_id
    #     HAVING total_spent > avg_customer_spend
    #     ORDER BY total_spent DESC""",
        
    # "Identify products that have been reviewed but never purchased":
    #     """SELECT p.product_id, p.name, COUNT(r.review_id) as review_count
    #     FROM products p
    #     JOIN reviews r ON p.product_id = r.product_id
    #     LEFT JOIN order_items oi ON p.product_id = oi.product_id
    #     WHERE oi.order_item_id IS NULL
    #     GROUP BY p.product_id
    #     ORDER BY review_count DESC""",
        
    # "Calculate the average time between registration and first purchase for each user":
    #     """SELECT u.user_id, u.username, u.registration_date,
    #     MIN(o.order_date) as first_purchase_date,
    #     JULIANDAY(MIN(o.order_date)) - JULIANDAY(u.registration_date) as days_to_first_purchase
    #     FROM users u
    #     LEFT JOIN orders o ON u.user_id = o.user_id
    #     WHERE o.payment_status = 'paid'
    #     GROUP BY u.user_id
    #     HAVING first_purchase_date IS NOT NULL
    #     ORDER BY days_to_first_purchase"""
}

# Complex Text2SQL prompt template
complex_text2sql_template = """You are an expert SQL query generator for an e-commerce database.
Given the following complex database schema:

{schema}

Generate a SQL query to answer the following question:
{question}

Return only the SQL query without any explanations.
"""

# Define function to get a specific model
def get_model(model_name):
    if model_name == "gpt-4o":
        return ChatOpenAI(model_name="gpt-4o", temperature=0)
    elif model_name == "deepseek":
        return OllamaLLM(model="deepseek-r1:7b", temperature=0)
    else:
        raise ValueError(f"Unsupported model: {model_name}")

# Function to run complex Text2SQL experiments with a single model
def run_complex_text2sql_experiment(model_name):
    session_counter = 1
    # Update project version name in the environment variable
    os.environ["FI_PROJECT_VERSION_NAME"] = model_name
    
    results = []
    model = get_model(model_name)
    
    # Create a SQLAlchemy engine for in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    
    # Split the schema into individual CREATE TABLE statements
    create_statements = COMPLEX_DB_SCHEMA.split(';')
    
    # Create tables using SQLAlchemy
    with engine.connect() as conn:
        # Execute each CREATE TABLE statement separately
        for statement in create_statements:
            statement = statement.strip()
            if statement:  # Skip empty statements
                conn.execute(text(statement))
        conn.commit()
        
        # Insert sample data
        for table_name, rows in COMPLEX_SAMPLE_DATA.items():
            if not rows or not isinstance(rows, list) or len(rows) == 0:
                continue
                
            # Get column names from the first row
            columns = list(rows[0].keys())
            
            # Insert data
            for row in rows:
                # Create a dictionary of column names to values
                params = {col: row[col] for col in columns}
                
                # Build the insert query with named parameters
                placeholders = ', '.join([f":{col}" for col in columns])
                column_str = ', '.join(columns)
                insert_query = f"INSERT INTO {table_name} ({column_str}) VALUES ({placeholders})"
                
                # Execute with parameters as a dictionary
                conn.execute(text(insert_query), params)
            
            conn.commit()
    
    # Create a LangChain SQLDatabase wrapper with the SQLAlchemy engine
    db = SQLDatabase(engine=engine)
    
    # Create SQL agent
    agent_executor = create_sql_agent(
        llm=model,
        db=db,
        agent_type="tool-calling",
        verbose=True,
        max_iterations=5
    )
    
    for question, ground_truth in COMPLEX_TEXT2SQL_GROUND_TRUTH.items():
        session_counter += 1
        
        start_time = time.time()
        try:
            # Execute the agent with the question
            agent_result = agent_executor.invoke({"input": question})
            
            end_time = time.time()
            latency = end_time - start_time
            
            # Extract the SQL query from the agent's intermediate steps
            sql_query = ""
            for step in agent_result.get("intermediate_steps", []):
                if isinstance(step[0].tool_input, str) and ("SELECT" in step[0].tool_input or "INSERT" in step[0].tool_input or "UPDATE" in step[0].tool_input):
                    sql_query = step[0].tool_input
                    break
            
            results.append({
                "model": model_name,
                "question": question,
                "generated_sql": sql_query,
                "ground_truth_sql": ground_truth,
                "execution_success": True,
                "result": agent_result["output"],
                "error": "",
                "latency": latency
            })
            
        except Exception as e:
            error_msg = str(e)
            results.append({
                "model": model_name,
                "question": question,
                "generated_sql": "Error: Could not extract SQL query",
                "ground_truth_sql": ground_truth,
                "execution_success": False,
                "result": "",
                "error": error_msg,
                "latency": time.time() - start_time
            })
        
        # finally:
        #     # Shutdown the tracer for this iteration
        #     LangChainInstrumentor().uninstrument()
    
    return pd.DataFrame(results)

def main():
    # Run Complex Text2SQL experiment with GPT-4o
    print("Running Complex Text2SQL Experiment with GPT-4o...")
    complex_text2sql_results = run_complex_text2sql_experiment("gpt-4o")
    complex_text2sql_results.to_csv("complex_text2sql_results_gpt4o.csv", index=False)
    
    # Calculate and print summary statistics
    print("\nComplex Text2SQL Performance Summary (GPT-4o):")
    successful_queries = complex_text2sql_results["execution_success"].sum()
    total_queries = len(complex_text2sql_results)
    success_rate = successful_queries / total_queries * 100
    
    stats = {
        "success_rate": f"{success_rate:.2f}%",
        "successful_queries": f"{successful_queries}/{total_queries}",
        "avg_latency": f"{complex_text2sql_results['latency'].mean():.2f}s"
    }
    print(stats)
    
    # Save summary
    summary = {
        "complex_text2sql": {
            "gpt-4o": {
                "success_rate": success_rate,
                "successful_queries": int(successful_queries),
                "total_queries": total_queries,
                "avg_latency": complex_text2sql_results["latency"].mean()
            }
        }
    }
    
    with open("complex_experiment_summary_gpt4o.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()