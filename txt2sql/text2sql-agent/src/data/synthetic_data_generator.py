"""
Synthetic Retail Data Generator for Text-to-SQL Agent

This module generates realistic synthetic retail data for testing and demonstration
purposes, including products, pricing, elasticity, competitive data, and sales metrics.
"""

import os
import sqlite3
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json


@dataclass
class ProductData:
    """Product information"""
    upc_code: str
    product_name: str
    brand: str
    category_level_1: str
    category_level_2: str
    category_level_3: str
    package_size: str
    unit_of_measure: str
    cost: float
    base_price: float


class SyntheticDataGenerator:
    """Generate synthetic retail data for the system"""
    
    def __init__(self, database_path: str = "retail_analytics.db"):
        """
        Initialize the synthetic data generator
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)
        
        # Data configuration
        self.num_products = 1000
        self.num_stores = 50
        self.num_competitors = 5
        self.weeks_of_data = 52  # 1 year of data
        
        # Random seed for reproducible data
        random.seed(42)
        np.random.seed(42)
        
        # Initialize data templates
        self._initialize_data_templates()
    
    def _initialize_data_templates(self):
        """Initialize data templates and reference data"""
        
        # Category hierarchy
        self.categories = {
            "GROCERY": {
                "BREAD & WRAPS": ["Bread", "Tortillas", "Bagels", "English Muffins"],
                "DAIRY": ["Milk", "Cheese", "Yogurt", "Butter"],
                "FROZEN FOOD": ["Ice Cream", "Frozen Vegetables", "Frozen Meals", "Frozen Pizza"],
                "BEVERAGES": ["Soft Drinks", "Juice", "Water", "Energy Drinks"],
                "SNACKS": ["Chips", "Crackers", "Nuts", "Candy"]
            },
            "PRODUCE": {
                "FRESH FRUITS": ["Apples", "Bananas", "Oranges", "Berries"],
                "FRESH VEGETABLES": ["Lettuce", "Tomatoes", "Carrots", "Onions"],
                "ORGANIC": ["Organic Apples", "Organic Spinach", "Organic Carrots"]
            },
            "MEAT & SEAFOOD": {
                "FRESH MEAT": ["Beef", "Chicken", "Pork", "Turkey"],
                "SEAFOOD": ["Salmon", "Shrimp", "Tuna", "Cod"],
                "DELI": ["Sliced Turkey", "Ham", "Roast Beef"]
            },
            "BAKERY": {
                "FRESH BAKED": ["Donuts", "Muffins", "Cookies", "Cakes"],
                "ARTISAN BREAD": ["Sourdough", "Whole Wheat", "Rye"]
            }
        }
        
        # Brand names
        self.brands = [
            "Great Value", "Kroger", "Kirkland", "365 Everyday Value", "Market Pantry",
            "Simply Balanced", "Good & Gather", "Essential Everyday", "Best Choice",
            "Our Brand", "Store Brand", "Premium Select", "Nature's Promise",
            "Coca-Cola", "Pepsi", "Kraft", "General Mills", "Kellogg's",
            "Nestle", "Unilever", "P&G", "Johnson & Johnson", "Mars"
        ]
        
        # Store zones/banners
        self.store_zones = [
            "Banner 1", "Banner 2", "Orange", "Blue", "Green", "Red",
            "Metro", "Suburban", "Rural", "Premium"
        ]
        
        # Competitors
        self.competitors = [
            "Walmart", "Target", "Kroger", "Safeway", "No Frills Ontario",
            "Costco", "Sam's Club", "Whole Foods", "Trader Joe's", "Aldi"
        ]
        
        # Price families (pricing strategy groups)
        self.price_families = [str(i) for i in range(7280, 7300)]
        
        # Unit of measure
        self.units_of_measure = ["EA", "LB", "OZ", "GAL", "QT", "PT", "PKG", "BOX", "BAG"]
    
    def generate_all_data(self):
        """Generate all synthetic data and populate the database"""
        self.logger.info("Starting synthetic data generation...")
        
        # Create database and tables
        self._create_database_schema()
        
        # Generate core data
        products = self._generate_products()
        stores = self._generate_stores()
        
        # Generate transactional data
        self._generate_pricing_data(products, stores)
        self._generate_elasticity_data(products)
        self._generate_competitive_data(products)
        self._generate_sales_data(products, stores)
        self._generate_margin_data(products, stores)
        
        self.logger.info("Synthetic data generation completed successfully")
    
    def _create_database_schema(self):
        """Create database tables with proper schema"""
        
        schema_sql = """
        -- Products table
        CREATE TABLE IF NOT EXISTS products (
            upc_code TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            brand TEXT,
            category_level_1 TEXT,
            category_level_2 TEXT,
            category_level_3 TEXT,
            package_size TEXT,
            unit_of_measure TEXT,
            cost REAL,
            base_price REAL,
            price_family TEXT,
            created_date DATE DEFAULT CURRENT_DATE
        );
        
        -- Stores table
        CREATE TABLE IF NOT EXISTS stores (
            store_id TEXT PRIMARY KEY,
            store_name TEXT NOT NULL,
            zone TEXT,
            banner TEXT,
            region TEXT,
            store_type TEXT,
            opened_date DATE
        );
        
        -- Pricing table
        CREATE TABLE IF NOT EXISTS pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc_code TEXT,
            store_id TEXT,
            price_date DATE,
            current_price REAL,
            suggested_price REAL,
            price_family TEXT,
            pricing_strategy TEXT,
            price_change_reason TEXT,
            units_impact REAL,
            revenue_impact REAL,
            FOREIGN KEY (upc_code) REFERENCES products(upc_code),
            FOREIGN KEY (store_id) REFERENCES stores(store_id)
        );
        
        -- Elasticity table
        CREATE TABLE IF NOT EXISTS elasticity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc_code TEXT,
            category_level_2 TEXT,
            elasticity_value REAL,
            elasticity_category TEXT,
            confidence_level REAL,
            last_updated DATE,
            FOREIGN KEY (upc_code) REFERENCES products(upc_code)
        );
        
        -- Competitive pricing table
        CREATE TABLE IF NOT EXISTS competitive_pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc_code TEXT,
            competitor_name TEXT,
            competitor_price REAL,
            our_price REAL,
            cpi_value REAL,
            price_gap REAL,
            price_gap_percent REAL,
            observation_date DATE,
            FOREIGN KEY (upc_code) REFERENCES products(upc_code)
        );
        
        -- Sales data table
        CREATE TABLE IF NOT EXISTS sales_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc_code TEXT,
            store_id TEXT,
            week_ending_date DATE,
            units_sold INTEGER,
            revenue REAL,
            forecast_units INTEGER,
            forecast_revenue REAL,
            FOREIGN KEY (upc_code) REFERENCES products(upc_code),
            FOREIGN KEY (store_id) REFERENCES stores(store_id)
        );
        
        -- Margin analysis table
        CREATE TABLE IF NOT EXISTS margin_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc_code TEXT,
            store_id TEXT,
            analysis_date DATE,
            cost REAL,
            selling_price REAL,
            margin_amount REAL,
            margin_percent REAL,
            margin_category TEXT,
            FOREIGN KEY (upc_code) REFERENCES products(upc_code),
            FOREIGN KEY (store_id) REFERENCES stores(store_id)
        );
        
        -- Price changes log
        CREATE TABLE IF NOT EXISTS price_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upc_code TEXT,
            store_id TEXT,
            change_date DATE,
            old_price REAL,
            new_price REAL,
            change_amount REAL,
            change_percent REAL,
            change_type TEXT,
            reason TEXT,
            FOREIGN KEY (upc_code) REFERENCES products(upc_code),
            FOREIGN KEY (store_id) REFERENCES stores(store_id)
        );
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_pricing_upc_date ON pricing(upc_code, price_date);
        CREATE INDEX IF NOT EXISTS idx_sales_upc_week ON sales_data(upc_code, week_ending_date);
        CREATE INDEX IF NOT EXISTS idx_competitive_upc_date ON competitive_pricing(upc_code, observation_date);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_level_1, category_level_2);
        CREATE INDEX IF NOT EXISTS idx_elasticity_category ON elasticity(category_level_2);
        """
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.executescript(schema_sql)
                conn.commit()
            self.logger.info("Database schema created successfully")
        except Exception as e:
            self.logger.error(f"Error creating database schema: {str(e)}")
            raise
    
    def _generate_products(self) -> List[ProductData]:
        """Generate synthetic product data"""
        products = []
        
        for i in range(self.num_products):
            # Generate UPC code
            upc_code = f"{random.randint(1000000000000, 9999999999999)}"
            
            # Select random category
            level_1 = random.choice(list(self.categories.keys()))
            level_2 = random.choice(list(self.categories[level_1].keys()))
            level_3 = random.choice(self.categories[level_1][level_2])
            
            # Generate product name
            brand = random.choice(self.brands)
            product_name = f"{brand} {level_3}"
            
            # Add variety to product names
            if random.random() < 0.3:
                varieties = ["Original", "Light", "Organic", "Premium", "Family Size", "Low Fat"]
                product_name += f" {random.choice(varieties)}"
            
            # Package size and unit
            unit = random.choice(self.units_of_measure)
            if unit in ["LB", "OZ"]:
                size = f"{random.randint(1, 32)} {unit}"
            elif unit in ["GAL", "QT", "PT"]:
                size = f"{random.randint(1, 4)} {unit}"
            else:
                size = f"{random.randint(1, 24)} {unit}"
            
            # Cost and base price
            cost = round(random.uniform(0.50, 25.00), 2)
            markup = random.uniform(1.2, 2.5)  # 20% to 150% markup
            base_price = round(cost * markup, 2)
            
            product = ProductData(
                upc_code=upc_code,
                product_name=product_name,
                brand=brand,
                category_level_1=level_1,
                category_level_2=level_2,
                category_level_3=level_3,
                package_size=size,
                unit_of_measure=unit,
                cost=cost,
                base_price=base_price
            )
            
            products.append(product)
        
        # Insert products into database
        self._insert_products(products)
        self.logger.info(f"Generated {len(products)} products")
        
        return products
    
    def _insert_products(self, products: List[ProductData]):
        """Insert products into database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for product in products:
                    price_family = random.choice(self.price_families)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO products 
                        (upc_code, product_name, brand, category_level_1, category_level_2, 
                         category_level_3, package_size, unit_of_measure, cost, base_price, price_family)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product.upc_code, product.product_name, product.brand,
                        product.category_level_1, product.category_level_2, product.category_level_3,
                        product.package_size, product.unit_of_measure, product.cost, 
                        product.base_price, price_family
                    ))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting products: {str(e)}")
            raise
    
    def _generate_stores(self) -> List[Dict[str, Any]]:
        """Generate synthetic store data"""
        stores = []
        
        for i in range(self.num_stores):
            store_id = f"STORE_{i+1:03d}"
            store_name = f"Store {i+1}"
            zone = random.choice(self.store_zones)
            banner = random.choice(["Banner 1", "Banner 2", "Banner 3"])
            region = random.choice(["North", "South", "East", "West", "Central"])
            store_type = random.choice(["Supermarket", "Hypermarket", "Convenience", "Express"])
            
            # Random opening date in the past 5 years
            opened_date = datetime.now() - timedelta(days=random.randint(30, 1825))
            
            store = {
                'store_id': store_id,
                'store_name': store_name,
                'zone': zone,
                'banner': banner,
                'region': region,
                'store_type': store_type,
                'opened_date': opened_date.strftime('%Y-%m-%d')
            }
            
            stores.append(store)
        
        # Insert stores into database
        self._insert_stores(stores)
        self.logger.info(f"Generated {len(stores)} stores")
        
        return stores
    
    def _insert_stores(self, stores: List[Dict[str, Any]]):
        """Insert stores into database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for store in stores:
                    cursor.execute("""
                        INSERT OR REPLACE INTO stores 
                        (store_id, store_name, zone, banner, region, store_type, opened_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        store['store_id'], store['store_name'], store['zone'],
                        store['banner'], store['region'], store['store_type'], store['opened_date']
                    ))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting stores: {str(e)}")
            raise
    
    def _generate_pricing_data(self, products: List[ProductData], stores: List[Dict[str, Any]]):
        """Generate pricing data for products across stores and time"""
        pricing_data = []
        
        # Generate pricing for last 52 weeks
        end_date = datetime.now()
        
        for week in range(self.weeks_of_data):
            week_date = end_date - timedelta(weeks=week)
            
            # Sample products for this week (not all products in all stores)
            sampled_products = random.sample(products, min(len(products), 800))
            
            for product in sampled_products:
                # Sample stores for this product
                sampled_stores = random.sample(stores, min(len(stores), 30))
                
                for store in sampled_stores:
                    # Price variation based on store zone and time
                    base_price = product.base_price
                    
                    # Zone-based pricing
                    zone_multiplier = {
                        "Banner 1": 1.0,
                        "Banner 2": 1.05,
                        "Orange": 0.95,
                        "Blue": 1.02,
                        "Green": 0.98,
                        "Red": 1.03,
                        "Metro": 1.10,
                        "Suburban": 1.00,
                        "Rural": 0.92,
                        "Premium": 1.15
                    }.get(store['zone'], 1.0)
                    
                    current_price = round(base_price * zone_multiplier * random.uniform(0.9, 1.1), 2)
                    
                    # Suggested price (optimization recommendation)
                    suggested_price = round(current_price * random.uniform(0.95, 1.08), 2)
                    
                    # Pricing strategy
                    strategies = ["Competitive", "Premium", "Value", "Promotional", "EDLP", "Hi-Lo"]
                    pricing_strategy = random.choice(strategies)
                    
                    # Price change reason
                    reasons = ["Competitive Response", "Cost Change", "Demand Optimization", 
                              "Promotional", "Seasonal", "Inventory Management"]
                    price_change_reason = random.choice(reasons)
                    
                    # Impact estimates
                    units_impact = round(random.uniform(-50, 100), 1)
                    revenue_impact = round(units_impact * current_price * random.uniform(0.8, 1.2), 2)
                    
                    pricing_record = {
                        'upc_code': product.upc_code,
                        'store_id': store['store_id'],
                        'price_date': week_date.strftime('%Y-%m-%d'),
                        'current_price': current_price,
                        'suggested_price': suggested_price,
                        'price_family': random.choice(self.price_families),
                        'pricing_strategy': pricing_strategy,
                        'price_change_reason': price_change_reason,
                        'units_impact': units_impact,
                        'revenue_impact': revenue_impact
                    }
                    
                    pricing_data.append(pricing_record)
        
        # Insert pricing data
        self._insert_pricing_data(pricing_data)
        self.logger.info(f"Generated {len(pricing_data)} pricing records")
    
    def _insert_pricing_data(self, pricing_data: List[Dict[str, Any]]):
        """Insert pricing data into database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for record in pricing_data:
                    cursor.execute("""
                        INSERT INTO pricing 
                        (upc_code, store_id, price_date, current_price, suggested_price, 
                         price_family, pricing_strategy, price_change_reason, units_impact, revenue_impact)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record['upc_code'], record['store_id'], record['price_date'],
                        record['current_price'], record['suggested_price'], record['price_family'],
                        record['pricing_strategy'], record['price_change_reason'],
                        record['units_impact'], record['revenue_impact']
                    ))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting pricing data: {str(e)}")
            raise
    
    def _generate_elasticity_data(self, products: List[ProductData]):
        """Generate price elasticity data for products"""
        elasticity_data = []
        
        for product in products:
            # Elasticity varies by category
            category_elasticity = {
                "BREAD & WRAPS": random.uniform(0.8, 1.5),
                "DAIRY": random.uniform(0.6, 1.2),
                "FROZEN FOOD": random.uniform(1.0, 1.8),
                "BEVERAGES": random.uniform(1.2, 2.0),
                "SNACKS": random.uniform(1.5, 2.5),
                "FRESH FRUITS": random.uniform(0.9, 1.6),
                "FRESH VEGETABLES": random.uniform(0.7, 1.3),
                "FRESH MEAT": random.uniform(0.5, 1.0),
                "SEAFOOD": random.uniform(0.8, 1.4),
                "FRESH BAKED": random.uniform(1.1, 1.9)
            }
            
            elasticity_value = category_elasticity.get(
                product.category_level_2, 
                random.uniform(0.8, 1.8)
            )
            
            # Categorize elasticity
            if elasticity_value < 1.0:
                elasticity_category = "Inelastic"
            elif elasticity_value < 1.5:
                elasticity_category = "Moderately Elastic"
            else:
                elasticity_category = "Highly Elastic"
            
            confidence_level = random.uniform(0.7, 0.95)
            
            elasticity_record = {
                'upc_code': product.upc_code,
                'category_level_2': product.category_level_2,
                'elasticity_value': round(elasticity_value, 3),
                'elasticity_category': elasticity_category,
                'confidence_level': round(confidence_level, 3),
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            elasticity_data.append(elasticity_record)
        
        # Insert elasticity data
        self._insert_elasticity_data(elasticity_data)
        self.logger.info(f"Generated {len(elasticity_data)} elasticity records")
    
    def _insert_elasticity_data(self, elasticity_data: List[Dict[str, Any]]):
        """Insert elasticity data into database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for record in elasticity_data:
                    cursor.execute("""
                        INSERT OR REPLACE INTO elasticity 
                        (upc_code, category_level_2, elasticity_value, elasticity_category, 
                         confidence_level, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        record['upc_code'], record['category_level_2'], record['elasticity_value'],
                        record['elasticity_category'], record['confidence_level'], record['last_updated']
                    ))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting elasticity data: {str(e)}")
            raise
    
    def _generate_competitive_data(self, products: List[ProductData]):
        """Generate competitive pricing data"""
        competitive_data = []
        
        # Sample products for competitive analysis
        sampled_products = random.sample(products, min(len(products), 500))
        
        for product in sampled_products:
            our_price = product.base_price
            
            for competitor in self.competitors:
                # Competitor pricing varies
                competitor_price = round(our_price * random.uniform(0.85, 1.20), 2)
                
                # Calculate CPI (Competitive Price Index)
                cpi_value = round(competitor_price / our_price, 3)
                
                # Price gap
                price_gap = round(competitor_price - our_price, 2)
                price_gap_percent = round((price_gap / our_price) * 100, 1)
                
                observation_date = datetime.now() - timedelta(days=random.randint(0, 30))
                
                competitive_record = {
                    'upc_code': product.upc_code,
                    'competitor_name': competitor,
                    'competitor_price': competitor_price,
                    'our_price': our_price,
                    'cpi_value': cpi_value,
                    'price_gap': price_gap,
                    'price_gap_percent': price_gap_percent,
                    'observation_date': observation_date.strftime('%Y-%m-%d')
                }
                
                competitive_data.append(competitive_record)
        
        # Insert competitive data
        self._insert_competitive_data(competitive_data)
        self.logger.info(f"Generated {len(competitive_data)} competitive pricing records")
    
    def _insert_competitive_data(self, competitive_data: List[Dict[str, Any]]):
        """Insert competitive data into database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for record in competitive_data:
                    cursor.execute("""
                        INSERT INTO competitive_pricing 
                        (upc_code, competitor_name, competitor_price, our_price, cpi_value, 
                         price_gap, price_gap_percent, observation_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record['upc_code'], record['competitor_name'], record['competitor_price'],
                        record['our_price'], record['cpi_value'], record['price_gap'],
                        record['price_gap_percent'], record['observation_date']
                    ))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting competitive data: {str(e)}")
            raise
    
    def _generate_sales_data(self, products: List[ProductData], stores: List[Dict[str, Any]]):
        """Generate sales data"""
        sales_data = []
        
        # Generate sales for last 26 weeks (6 months)
        end_date = datetime.now()
        
        for week in range(26):
            week_ending = end_date - timedelta(weeks=week)
            
            # Sample products and stores
            sampled_products = random.sample(products, min(len(products), 600))
            
            for product in sampled_products:
                sampled_stores = random.sample(stores, min(len(stores), 20))
                
                for store in sampled_stores:
                    # Sales vary by category and seasonality
                    base_units = random.randint(10, 500)
                    
                    # Seasonal adjustment
                    month = week_ending.month
                    seasonal_multiplier = 1.0
                    if month in [11, 12]:  # Holiday season
                        seasonal_multiplier = 1.3
                    elif month in [6, 7, 8]:  # Summer
                        seasonal_multiplier = 1.1
                    
                    units_sold = int(base_units * seasonal_multiplier * random.uniform(0.7, 1.4))
                    revenue = round(units_sold * product.base_price, 2)
                    
                    # Forecast (slightly different from actual)
                    forecast_units = int(units_sold * random.uniform(0.9, 1.1))
                    forecast_revenue = round(forecast_units * product.base_price, 2)
                    
                    sales_record = {
                        'upc_code': product.upc_code,
                        'store_id': store['store_id'],
                        'week_ending_date': week_ending.strftime('%Y-%m-%d'),
                        'units_sold': units_sold,
                        'revenue': revenue,
                        'forecast_units': forecast_units,
                        'forecast_revenue': forecast_revenue
                    }
                    
                    sales_data.append(sales_record)
        
        # Insert sales data
        self._insert_sales_data(sales_data)
        self.logger.info(f"Generated {len(sales_data)} sales records")
    
    def _insert_sales_data(self, sales_data: List[Dict[str, Any]]):
        """Insert sales data into database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for record in sales_data:
                    cursor.execute("""
                        INSERT INTO sales_data 
                        (upc_code, store_id, week_ending_date, units_sold, revenue, 
                         forecast_units, forecast_revenue)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record['upc_code'], record['store_id'], record['week_ending_date'],
                        record['units_sold'], record['revenue'], record['forecast_units'],
                        record['forecast_revenue']
                    ))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting sales data: {str(e)}")
            raise
    
    def _generate_margin_data(self, products: List[ProductData], stores: List[Dict[str, Any]]):
        """Generate margin analysis data"""
        margin_data = []
        
        # Generate margin data for recent dates
        for days_ago in range(0, 90, 7):  # Weekly for last 3 months
            analysis_date = datetime.now() - timedelta(days=days_ago)
            
            sampled_products = random.sample(products, min(len(products), 400))
            
            for product in sampled_products:
                sampled_stores = random.sample(stores, min(len(stores), 15))
                
                for store in sampled_stores:
                    cost = product.cost
                    selling_price = round(product.base_price * random.uniform(0.95, 1.1), 2)
                    
                    margin_amount = round(selling_price - cost, 2)
                    margin_percent = round((margin_amount / selling_price) * 100, 1) if selling_price > 0 else 0
                    
                    # Categorize margin
                    if margin_percent < 10:
                        margin_category = "Low"
                    elif margin_percent < 25:
                        margin_category = "Medium"
                    else:
                        margin_category = "High"
                    
                    margin_record = {
                        'upc_code': product.upc_code,
                        'store_id': store['store_id'],
                        'analysis_date': analysis_date.strftime('%Y-%m-%d'),
                        'cost': cost,
                        'selling_price': selling_price,
                        'margin_amount': margin_amount,
                        'margin_percent': margin_percent,
                        'margin_category': margin_category
                    }
                    
                    margin_data.append(margin_record)
        
        # Insert margin data
        self._insert_margin_data(margin_data)
        self.logger.info(f"Generated {len(margin_data)} margin analysis records")
    
    def _insert_margin_data(self, margin_data: List[Dict[str, Any]]):
        """Insert margin data into database"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                for record in margin_data:
                    cursor.execute("""
                        INSERT INTO margin_analysis 
                        (upc_code, store_id, analysis_date, cost, selling_price, 
                         margin_amount, margin_percent, margin_category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record['upc_code'], record['store_id'], record['analysis_date'],
                        record['cost'], record['selling_price'], record['margin_amount'],
                        record['margin_percent'], record['margin_category']
                    ))
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting margin data: {str(e)}")
            raise
    
    def add_specific_test_data(self):
        """Add specific test data for the sample questions"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Add specific UPC code from sample questions
                cursor.execute("""
                    INSERT OR REPLACE INTO products 
                    (upc_code, product_name, brand, category_level_1, category_level_2, 
                     category_level_3, package_size, unit_of_measure, cost, base_price, price_family)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "0020282000000", "Wonder Bread Classic White", "Wonder", "GROCERY", 
                    "BREAD & WRAPS", "Bread", "20 OZ", "EA", 1.25, 2.49, "7286"
                ))
                
                # Add current pricing for this product
                cursor.execute("""
                    INSERT OR REPLACE INTO pricing 
                    (upc_code, store_id, price_date, current_price, suggested_price, 
                     price_family, pricing_strategy, price_change_reason, units_impact, revenue_impact)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "0020282000000", "STORE_001", datetime.now().strftime('%Y-%m-%d'),
                    2.49, 2.39, "7286", "Competitive", "Market Analysis", 15.2, 37.85
                ))
                
                # Add elasticity data
                cursor.execute("""
                    INSERT OR REPLACE INTO elasticity 
                    (upc_code, category_level_2, elasticity_value, elasticity_category, 
                     confidence_level, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "0020282000000", "BREAD & WRAPS", 1.15, "Moderately Elastic", 0.87,
                    datetime.now().strftime('%Y-%m-%d')
                ))
                
                conn.commit()
                
            self.logger.info("Added specific test data for sample questions")
            
        except Exception as e:
            self.logger.error(f"Error adding specific test data: {str(e)}")
            raise
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of generated data"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                summary = {}
                
                # Count records in each table
                tables = ['products', 'stores', 'pricing', 'elasticity', 
                         'competitive_pricing', 'sales_data', 'margin_analysis']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    summary[table] = count
                
                # Get date ranges
                cursor.execute("SELECT MIN(price_date), MAX(price_date) FROM pricing")
                price_date_range = cursor.fetchone()
                summary['pricing_date_range'] = price_date_range
                
                cursor.execute("SELECT MIN(week_ending_date), MAX(week_ending_date) FROM sales_data")
                sales_date_range = cursor.fetchone()
                summary['sales_date_range'] = sales_date_range
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Error getting data summary: {str(e)}")
            return {}


# Main execution function
def generate_synthetic_data(database_path: str = "retail_analytics.db"):
    """
    Generate all synthetic retail data
    
    Args:
        database_path: Path to SQLite database file
    """
    logging.basicConfig(level=logging.INFO)
    
    generator = SyntheticDataGenerator(database_path)
    
    print("Generating synthetic retail data...")
    print("=" * 50)
    
    # Generate all data
    generator.generate_all_data()
    
    # Add specific test data
    generator.add_specific_test_data()
    
    # Print summary
    summary = generator.get_data_summary()
    print("\nData Generation Summary:")
    print("-" * 30)
    for table, count in summary.items():
        if isinstance(count, int):
            print(f"{table}: {count:,} records")
        else:
            print(f"{table}: {count}")
    
    print("\nSynthetic data generation completed successfully!")
    return summary


if __name__ == "__main__":
    generate_synthetic_data()

