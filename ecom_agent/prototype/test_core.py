import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the current directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from memory import Memory
from reflection import Reflection
from planner import Planner
from router import Router

class TestMemory(unittest.TestCase):
    """Test cases for Memory module"""
    
    def setUp(self):
        self.memory = Memory()
    
    def test_add_and_get(self):
        """Test adding and retrieving memory entries"""
        # Add an entry
        entry = self.memory.add("test", "Test content")
        
        # Check entry structure
        self.assertEqual(entry["type"], "test")
        self.assertEqual(entry["content"], "Test content")
        self.assertIn("timestamp", entry)
        
        # Get all entries
        all_entries = self.memory.get_all()
        self.assertEqual(len(all_entries), 1)
        self.assertEqual(all_entries[0]["content"], "Test content")
        
        # Add another entry
        self.memory.add("test2", "Another test")
        
        # Get by type
        test_entries = self.memory.get_by_type("test")
        self.assertEqual(len(test_entries), 1)
        self.assertEqual(test_entries[0]["content"], "Test content")
        
        # Get recent entries
        recent = self.memory.get_recent(1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["content"], "Another test")
    
    def test_clear(self):
        """Test clearing memory"""
        # Add entries
        self.memory.add("test", "Test content")
        self.memory.add("test2", "Another test")
        
        # Verify entries exist
        self.assertEqual(len(self.memory.get_all()), 2)
        
        # Clear memory
        self.memory.clear()
        
        # Verify memory is empty
        self.assertEqual(len(self.memory.get_all()), 0)

class TestReflection(unittest.TestCase):
    """Test cases for Reflection module"""
    
    def setUp(self):
        self.reflection = Reflection()
    
    def test_reflect(self):
        """Test reflection on an action"""
        # Perform reflection
        action = "search for products"
        result = "Found 3 products"
        context = {"query": "shoes"}
        
        reflection = self.reflection.reflect(action, result, context)
        
        # Check reflection structure
        self.assertEqual(reflection["action"], action)
        self.assertTrue(reflection["success"])
        self.assertIn("improvements", reflection)
        self.assertIn("timestamp", reflection)
    
    def test_get_reflections(self):
        """Test retrieving reflections"""
        # Add reflections
        self.reflection.reflect("action1", "result1", {})
        self.reflection.reflect("action2", "result2", {})
        
        # Get all reflections
        all_reflections = self.reflection.get_all_reflections()
        self.assertEqual(len(all_reflections), 2)
        
        # Get recent reflections
        recent = self.reflection.get_recent_reflections(1)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["action"], "action2")
    
    def test_summarize(self):
        """Test summarizing reflections"""
        # Add reflections
        self.reflection.reflect("action1", "result1", {})
        self.reflection.reflect("action2", "error", {})
        
        # Get summary
        summary = self.reflection.summarize_reflections()
        
        # Check summary content
        self.assertIn("Reflection Summary", summary)
        self.assertIn("Total actions: 2", summary)
        self.assertIn("Successful actions:", summary)
        self.assertIn("Failed actions:", summary)

class TestPlanner(unittest.TestCase):
    """Test cases for Planner module"""
    
    def setUp(self):
        self.planner = Planner()
    
    def test_create_plan(self):
        """Test creating a plan"""
        # Create a plan
        task_id = "test_task"
        description = "Search for products"
        
        plan = self.planner.create_plan(task_id, description)
        
        # Check plan structure
        self.assertEqual(plan["task_id"], task_id)
        self.assertEqual(plan["description"], description)
        self.assertIn("steps", plan)
        self.assertEqual(plan["current_step"], 0)
        self.assertEqual(len(plan["completed_steps"]), 0)
        self.assertEqual(plan["status"], "created")
    
    def test_update_step(self):
        """Test updating a step in a plan"""
        # Create a plan
        task_id = "test_task"
        self.planner.create_plan(task_id, "Search for products")
        
        # Update a step
        updated_plan = self.planner.update_step(task_id, 0, "completed", {"result": "Step completed"})
        
        # Check updated plan
        self.assertEqual(updated_plan["steps"][0]["status"], "completed")
        self.assertIn("result", updated_plan["steps"][0])
        self.assertEqual(len(updated_plan["completed_steps"]), 1)
        
        # Update next step
        self.planner.update_step(task_id, 1, "completed")
        
        # Get the plan
        plan = self.planner.get_plan(task_id)
        self.assertEqual(len(plan["completed_steps"]), 2)

class TestRouter(unittest.TestCase):
    """Test cases for Router module"""
    
    def setUp(self):
        self.router = Router()
        
        # Define mock handlers
        self.search_handler = MagicMock(return_value={"type": "search_results"})
        self.order_handler = MagicMock(return_value={"type": "order_confirmation"})
        
        # Register skills
        self.router.register_skill("search", self.search_handler, ["search", "find"])
        self.router.register_skill("order", self.order_handler, ["buy", "purchase"])
    
    def test_route_exact_match(self):
        """Test routing with exact keyword match"""
        # Route a search query
        query = "search for shoes"
        context = {"query": query}
        
        skill_name, result = self.router.route(query, context)
        
        # Check routing result
        self.assertEqual(skill_name, "search")
        self.assertEqual(result["type"], "search_results")
        self.search_handler.assert_called_once_with(query, context)
    
    def test_route_no_match(self):
        """Test routing with no match"""
        # Route a query with no matching keywords
        query = "hello there"
        context = {"query": query}
        
        skill_name, result = self.router.route(query, context)
        
        # Check routing result
        self.assertEqual(skill_name, "default")
        self.assertIsNone(result)
        self.search_handler.assert_not_called()
        self.order_handler.assert_not_called()
    
    def test_route_best_match(self):
        """Test routing with best match selection"""
        # Add a skill with overlapping keywords
        recommend_handler = MagicMock(return_value={"type": "recommendations"})
        self.router.register_skill("recommend", recommend_handler, ["find products", "recommend"])
        
        # Route a query with multiple potential matches
        query = "find products to buy"
        context = {"query": query}
        
        skill_name, result = self.router.route(query, context)
        
        # Check routing result - should match "find products" from recommend skill
        self.assertEqual(skill_name, "recommend")
        self.assertEqual(result["type"], "recommendations")

if __name__ == "__main__":
    unittest.main()
