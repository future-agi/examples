import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the current directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from image_processor import ImageProcessor
from product_recommender import ProductRecommender

class MockResponse:
    def __init__(self, content, created=1234567890):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content
        self.created = created
        self.data = [MagicMock()]
        self.data[0].url = "https://example.com/image.png"

class TestImageProcessor(unittest.TestCase):
    """Test cases for ImageProcessor module"""
    
    @patch('openai.chat.completions.create')
    @patch('openai.api_key', 'fake-api-key')
    def test_analyze_image(self, mock_create):
        """Test image analysis"""
        # Setup mock
        mock_create.return_value = MockResponse("This is a red shirt with blue stripes.")
        
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_img:
            # Write some dummy data to the file
            temp_img.write(b'dummy image data')
            temp_img.flush()
            
            # Initialize processor
            processor = ImageProcessor()
            
            # Analyze image
            result = processor.analyze_image(temp_img.name)
            
            # Check result
            self.assertIn('description', result)
            self.assertEqual(result['description'], "This is a red shirt with blue stripes.")
            self.assertIn('detected_objects', result)
            self.assertIn('timestamp', result)
    
    @patch('openai.chat.completions.create')
    @patch('openai.api_key', 'fake-api-key')
    def test_generate_product_recommendation(self, mock_create):
        """Test product recommendation generation"""
        # Setup mock
        mock_create.return_value = MockResponse("I recommend a blue shirt to complement your style.")
        
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_img:
            # Write some dummy data to the file
            temp_img.write(b'dummy image data')
            temp_img.flush()
            
            # Initialize processor with mocked analyze_image
            processor = ImageProcessor()
            processor.analyze_image = MagicMock(return_value={
                'description': 'A person wearing casual clothes',
                'detected_objects': ['person', 'shirt']
            })
            
            # Generate recommendations
            result = processor.generate_product_recommendation(temp_img.name, "casual outfit")
            
            # Check result
            self.assertIn('recommendations', result)
            self.assertEqual(result['recommendations'], "I recommend a blue shirt to complement your style.")
            self.assertTrue(result['based_on_image'])
            self.assertIn('detected_objects', result)
            self.assertIn('timestamp', result)
    
    @patch('openai.images.edit')
    @patch('requests.get')
    @patch('openai.api_key', 'fake-api-key')
    def test_render_product_on_image(self, mock_get, mock_edit):
        """Test product rendering on image"""
        # Setup mocks
        mock_edit.return_value = MockResponse("", 1234567890)
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.content = b'rendered image data'
        mock_get.return_value = mock_response
        
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_img:
            # Write some dummy data to the file
            temp_img.write(b'dummy image data')
            temp_img.flush()
            
            # Initialize processor
            processor = ImageProcessor()
            
            # Create directory for rendered products
            os.makedirs('rendered_products', exist_ok=True)
            
            # Render product on image
            output_path, result = processor.render_product_on_image(temp_img.name, "A blue shirt")
            
            # Check result
            self.assertTrue(output_path.startswith('rendered_products/'))
            self.assertEqual(result['original_image'], temp_img.name)
            self.assertEqual(result['product_description'], "A blue shirt")
            self.assertEqual(result['rendered_image_path'], output_path)
            self.assertIn('timestamp', result)

class TestProductRecommender(unittest.TestCase):
    """Test cases for ProductRecommender module"""
    
    def setUp(self):
        # Create mock memory and reflection systems
        self.memory = MagicMock()
        self.reflection = MagicMock()
        
        # Create mock image processor
        self.image_processor = MagicMock()
        
        # Initialize recommender with mocks
        self.recommender = ProductRecommender(self.memory, self.reflection)
        self.recommender.image_processor = self.image_processor
    
    def test_analyze_user_image(self):
        """Test user image analysis"""
        # Setup mock
        self.image_processor.analyze_image.return_value = {
            'description': 'A person wearing casual clothes',
            'detected_objects': ['person', 'shirt']
        }
        
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_img:
            # Write some dummy data to the file
            temp_img.write(b'dummy image data')
            temp_img.flush()
            
            # Analyze image
            result = self.recommender.analyze_user_image(temp_img.name, "casual outfit")
            
            # Check result
            self.assertEqual(result['description'], "A person wearing casual clothes")
            self.assertIn('detected_objects', result)
            
            # Verify memory was updated
            self.memory.add.assert_called_once()
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        # Setup mock
        self.image_processor.generate_product_recommendation.return_value = {
            'recommendations': 'I recommend a blue shirt',
            'based_on_image': True,
            'detected_objects': ['shirt']
        }
        
        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_img:
            # Write some dummy data to the file
            temp_img.write(b'dummy image data')
            temp_img.flush()
            
            # Generate recommendations
            result = self.recommender.generate_recommendations(temp_img.name, "casual outfit")
            
            # Check result
            self.assertEqual(result['recommendations'], "I recommend a blue shirt")
            self.assertTrue(result['based_on_image'])
            
            # Verify memory was updated
            self.memory.add.assert_called_once()
            
            # Verify reflection was performed
            self.reflection.reflect.assert_called_once()
    
    def test_ask_for_rendering(self):
        """Test asking for rendering confirmation"""
        # Setup test data
        image_path = "/path/to/image.jpg"
        recommendations = {'recommendations': 'I recommend a blue shirt'}
        
        # Ask for rendering
        message, request_id = self.recommender.ask_for_rendering(image_path, recommendations)
        
        # Check result
        self.assertIn("Would you like me to create a visualization", message)
        self.assertTrue(request_id.startswith("render_"))
        
        # Verify request was stored
        self.assertIn(request_id, self.recommender.render_requests)
        self.assertEqual(self.recommender.render_requests[request_id]['image_path'], image_path)
        self.assertEqual(self.recommender.render_requests[request_id]['recommendations'], recommendations)
        self.assertEqual(self.recommender.render_requests[request_id]['status'], "pending")
    
    def test_create_product_rendering(self):
        """Test product rendering creation"""
        # Setup mocks
        self.image_processor.render_product_on_image.return_value = (
            "/path/to/rendered.jpg",
            {'rendered_image_path': '/path/to/rendered.jpg'}
        )
        
        # Setup test data
        request_id = "render_0"
        image_path = "/path/to/image.jpg"
        recommendations = {'recommendations': 'I recommend a blue shirt'}
        
        # Store a request
        self.recommender.render_requests[request_id] = {
            'image_path': image_path,
            'recommendations': recommendations,
            'status': 'pending'
        }
        
        # Create rendering
        rendered_path, result = self.recommender.create_product_rendering(request_id, "A blue shirt")
        
        # Check result
        self.assertEqual(rendered_path, "/path/to/rendered.jpg")
        self.assertEqual(result['rendered_image_path'], "/path/to/rendered.jpg")
        
        # Verify request was updated
        self.assertEqual(self.recommender.render_requests[request_id]['status'], "completed")
        
        # Verify memory was updated
        self.memory.add.assert_called_once()

if __name__ == "__main__":
    unittest.main()
