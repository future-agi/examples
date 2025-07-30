#!/usr/bin/env python3
"""
Database initialization script for NotebookLM
Creates all tables and sets up initial data
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app, db, User, Notebook, Source, Conversation, GeneratedContent, Podcast

def init_database():
    """Initialize the database with tables and sample data"""
    with app.app_context():
        print("Creating database tables...")
        
        # Drop all tables (for development)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Tables created successfully!")
        
        # Create sample users
        print("Creating sample users...")
        
        # Test user
        test_user = User(
            name="Test User",
            email="test@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(test_user)
        
        # Enterprise user (premium features)
        enterprise_user = User(
            name="Enterprise User",
            email="enterprise@example.com",
            password_hash=generate_password_hash("enterprise123"),
            plan="enterprise"
        )
        db.session.add(enterprise_user)
        
        # Demo user with sample data
        demo_user = User(
            name="Demo User",
            email="demo@example.com",
            password_hash=generate_password_hash("demo123")
        )
        db.session.add(demo_user)
        
        db.session.commit()
        print("Sample users created!")
        
        # Create sample notebook for demo user
        print("Creating sample notebook...")
        
        sample_notebook = Notebook(
            title="Sample Research Notebook",
            description="A demonstration notebook showing NotebookLM capabilities",
            user_id=demo_user.id
        )
        db.session.add(sample_notebook)
        db.session.commit()
        
        print("Sample notebook created!")
        
        print("\nDatabase initialization complete!")
        print("\nSample accounts:")
        print("- test@example.com / password123 (Regular user)")
        print("- enterprise@example.com / enterprise123 (Enterprise user with unlimited features)")
        print("- demo@example.com / demo123 (Demo user with sample data)")

def reset_database():
    """Reset the database (drop and recreate all tables)"""
    with app.app_context():
        print("Resetting database...")
        db.drop_all()
        db.create_all()
        print("Database reset complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        init_database()

