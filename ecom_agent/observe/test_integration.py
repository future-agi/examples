import os
import unittest
from unittest.mock import patch, MagicMock

# Add the current directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from main import EcommerceAgent, EcommerceSkills

class TestEcommerceSkills(unittest.TestCase):
    """Test cases for EcommerceSkills class"""
    
    def setUp(self):
        # Create mock memory, reflection, and planner
        self.memory = MagicMock()
        self.reflection = MagicMock()
        self.planner = MagicMock()
        self.planner.create_plan.return_value = {
            "task_id": "test_task",
            "steps": [{"id": 0}, {"id": 1}, {"id": 2}, {"id": 3}]
        }
        
        # Initialize skills
        self.skills = EcommerceSkills(self.memory, self.reflection, self.planner)
        
        # Mock the image processor and product recommender
        self.skills.image_processor = MagicMock()
        self.skills.product_recommender = MagicMock()
    
    def test_search_skill(self):
        """Test search skill"""
        # Execute search skill
        query = "search for shoes"
        context = {"query": query}
        
        result = self.skills.search_skill(query, context)
        
        # Check result
        self.assertEqual(result["type"], "search_results")
        self.assertEqual(result["query"], query)
        self.assertIn("results", result)
        self.assertIn("plan", result)
        
        # Verify planner was used
        self.planner.create_plan.assert_called_once()
        self.assertEqual(self.planner.update_step.call_count, 5)  # 5 steps in search plan
        
        # Verify memory was updated
        self.memory.add.assert_called_once()
        
        # Verify reflection was performed
        self.reflection.reflect.assert_called_once()
    
    def test_place_order_skill(self):
        """Test place order skill"""
        # Execute place order skill
        query = "buy shoes"
        context = {"query": query}
        
        result = self.skills.place_order_skill(query, context)
        
        # Check result
        self.assertEqual(result["type"], "order_confirmation")
        self.assertIn("order_id", result)
        self.assertIn("product", result)
        self.assertIn("total", result)
        self.assertEqual(result["status"], "confirmed")
        
        # Verify planner was used
        self.planner.create_plan.assert_called_once()
        self.assertEqual(self.planner.update_step.call_count, 7)  # 7 steps in order plan
        
        # Verify memory was updated
        self.memory.add.assert_called_once()
        
        # Verify reflection was performed
        self.reflection.reflect.assert_called_once()
    
    def test_search_order_skill(self):
        """Test search order skill"""
        # Execute search order skill
        query = "find my order ORD-1001"
        context = {"query": query}
        
        result = self.skills.search_order_skill(query, context)
        
        # Check result
        self.assertEqual(result["type"], "order_details")
        self.assertEqual(result["query"], query)
        self.assertIn("order", result)
        self.assertEqual(result["order"]["order_id"], "ORD-1001")
        
        # Verify planner was used
        self.planner.create_plan.assert_called_once()
        self.assertEqual(self.planner.update_step.call_count, 4)  # 4 steps in search order plan
        
        # Verify memory was updated
        self.memory.add.assert_called_once()
        
        # Verify reflection was performed
        self.reflection.reflect.assert_called_once()
    
    def test_cancel_order_skill(self):
        """Test cancel order skill"""
        # Execute cancel order skill
        query = "cancel my order ORD-1001"
        context = {"query": query}
        
        result = self.skills.cancel_order_skill(query, context)
        
        # Check result
        self.assertEqual(result["type"], "order_cancellation")
        self.assertEqual(result["query"], query)
        self.assertEqual(result["order_id"], "ORD-1001")
        self.assertEqual(result["status"], "cancelled")
        self.assertIn("refund_amount", result)
        
        # Verify planner was used
        self.planner.create_plan.assert_called_once()
        self.assertEqual(self.planner.update_step.call_count, 4)  # 4 steps in cancel order plan
        
        # Verify memory was updated
        self.memory.add.assert_called_once()
        
        # Verify reflection was performed
        self.reflection.reflect.assert_called_once()
    
    def test_recommendation_skill_without_image(self):
        """Test recommendation skill without image"""
        # Execute recommendation skill
        query = "recommend casual clothes"
        context = {"query": query}
        
        result = self.skills.recommendation_skill(query, context)
        
        # Check result
        self.assertEqual(result["type"], "product_recommendation")
        self.assertEqual(result["query"], query)
        self.assertFalse(result["image_based"])
        self.assertIn("recommendations", result)
        
        # Verify planner was used
        self.planner.create_plan.assert_called_once()
        self.assertEqual(self.planner.update_step.call_count, 6)  # 6 steps in recommendation plan
        
        # Verify memory was updated
        self.memory.add.assert_called_once()
        
        # Verify reflection was performed
        self.reflection.reflect.assert_called_once()
    
    def test_recommendation_skill_with_image(self):
        """Test recommendation skill with image"""
        # Setup mocks
        self.product_recommender.analyze_user_image.return_value = {"description": "A person in casual clothes"}
        self.product_recommender.generate_recommendations.return_value = {"recommendations": "I recommend a blue shirt"}
        self.product_recommender.ask_for_rendering.return_value = ("Would you like a visualization?", "render_0")
        
        # Create a temporary image file
        with open("/tmp/test_image.jpg", "w") as f:
            f.write("dummy image data")
        
        # Execute recommendation skill
        query = "recommend clothes that match this"
        context = {"query": query, "image_path": "/tmp/test_image.jpg"}
        
        result = self.skills.recommendation_skill(query, context)
        
        # Check result
        self.assertEqual(result["type"], "product_recommendation")
        self.assertEqual(result["query"], query)
        self.assertTrue(result["image_based"])
        self.assertIn("analysis", result)
        self.assertIn("recommendations", result)
        self.assertIn("render_message", result)
        self.assertEqual(result["render_request_id"], "render_0")
        
        # Verify product recommender was used
        self.product_recommender.analyze_user_image.assert_called_once()
        self.product_recommender.generate_recommendations.assert_called_once()
        self.product_recommender.ask_for_rendering.assert_called_once()
        
        # Verify planner was used
        self.planner.create_plan.assert_called_once()
        self.assertEqual(self.planner.update_step.call_count, 4)  # 4 steps completed in recommendation plan
        
        # Verify memory was updated
        self.memory.add.assert_called_once()
        
        # Verify reflection was performed
        self.reflection.reflect.assert_called_once()
        
        # Clean up
        os.remove("/tmp/test_image.jpg")
    
    def test_process_render_response_yes(self):
        """Test processing a positive render response"""
        # Setup mocks
        request_id = "render_0"
        self.product_recommender.get_rendering_request.return_value = {
            "image_path": "/tmp/test_image.jpg",
            "recommendations": {"recommendations": "I recommend a blue shirt"}
        }
        self.product_recommender.create_product_rendering.return_value = (
            "/path/to/rendered.jpg",
            {"rendered_image_path": "/path/to/rendered.jpg"}
        )
        
        # Process render response
        result = self.skills.process_render_response(request_id, "yes", {})
        
        # Check result
        self.assertEqual(result["type"], "product_rendering")
        self.assertEqual(result["request_id"], request_id)
        self.assertEqual(result["rendered_image_path"], "/path/to/rendered.jpg")
        
        # Verify product recommender was used
        self.product_recommender.get_rendering_request.assert_called_once()
        self.product_recommender.create_product_rendering.assert_called_once()
        
        # Verify memory was updated
        self.memory.add.assert_called_once()
    
    def test_process_render_response_no(self):
        """Test processing a negative render response"""
        # Setup mocks
        request_id = "render_0"
        self.product_recommender.get_rendering_request.return_value = {
            "image_path": "/tmp/test_image.jpg",
            "recommendations": {"recommendations": "I recommend a blue shirt"}
        }
        
        # Process render response
        result = self.skills.process_render_response(request_id, "no", {})
        
        # Check result
        self.assertEqual(result["type"], "rendering_declined")
        self.assertEqual(result["request_id"], request_id)
        self.assertIn("message", result)
        
        # Verify product recommender was used
        self.product_recommender.get_rendering_request.assert_called_once()
        self.product_recommender.create_product_rendering.assert_not_called()
        
        # Verify memory was updated
        self.memory.add.assert_called_once()

class TestEcommerceAgent(unittest.TestCase):
    """Test cases for EcommerceAgent class"""
    
    def setUp(self):
        # Mock the router
        self.router_patcher = patch('main.Router')
        self.mock_router = self.router_patcher.start()
        
        # Mock the skills
        self.skills_patcher = patch('main.EcommerceSkills')
        self.mock_skills = self.skills_patcher.start()
        
        # Initialize agent
        self.agent = EcommerceAgent()
    
    def tearDown(self):
        self.router_patcher.stop()
        self.skills_patcher.stop()
    
    def test_process_query_without_image(self):
        """Test processing a query without an image"""
        # Setup mocks
        self.agent.router.route.return_value = ("search", {"type": "search_results", "results": []})
        
        # Process query
        response, rendered_image = self.agent.process_query("search for shoes")
        
        # Check result
        self.assertIn("search results", response.lower())
        self.assertIsNone(rendered_image)
        
        # Verify router was used
        self.agent.router.route.assert_called_once()
    
    def test_process_query_with_image(self):
        """Test processing a query with an image"""
        # Setup mocks
        self.agent.router.route.return_value = ("recommendation", {
            "type": "product_recommendation",
            "render_message": "Would you like a visualization?",
            "render_request_id": "render_0"
        })
        
        # Process query
        response, rendered_image = self.agent.process_query("recommend clothes", "/tmp/test_image.jpg")
        
        # Check result
        self.assertEqual(response, "Would you like a visualization?")
        self.assertIsNone(rendered_image)
        self.assertEqual(self.agent.active_render_request, "render_0")
        
        # Verify router was used
        self.agent.router.route.assert_called_once()
        
        # Verify memory was updated
        self.agent.memory.add.assert_called_once()
    
    def test_process_render_response(self):
        """Test processing a response to a render request"""
        # Setup state
        self.agent.active_render_request = "render_0"
        
        # Setup mocks
        self.agent.skills.process_render_response.return_value = {
            "type": "product_rendering",
            "rendered_image_path": "/path/to/rendered.jpg"
        }
        
        # Process query (as a response to render request)
        response, rendered_image = self.agent.process_query("yes")
        
        # Check result
        self.assertIn("visualization", response.lower())
        self.assertEqual(rendered_image, "/path/to/rendered.jpg")
        self.assertIsNone(self.agent.active_render_request)  # Should be cleared
        
        # Verify skills were used
        self.agent.skills.process_render_response.assert_called_once()
        
        # Verify router was not used
        self.agent.router.route.assert_not_called()

if __name__ == "__main__":
    unittest.main()
