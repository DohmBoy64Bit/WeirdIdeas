import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db, login_manager
from backend.models.user import User
from backend.models.content import Post, Comment
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class CoreFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_login(self):
        # Register
        self.client.post('/register', data={
            'username': 'SurvivorSteve',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Login
        return self.client.post('/login', data={
            'username': 'SurvivorSteve',
            'password': 'password123'
        }, follow_redirects=True)

    def test_health(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'healthy', response.data)

    def test_auth_flow(self):
        # Initial register
        response = self.register_login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SurvivorSteve', response.data)
        
        # Verify DB
        user = User.query.filter_by(username='SurvivorSteve').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_zombie)

    def test_post_creation(self):
        self.register_login()
        
        with patch('backend.logic.orchestrator.Orchestrator.process_new_post') as mock_process:
            response = self.client.post('/create_post', data={
                'title': 'Test Moan',
                'body': 'This is a test body.',
                'subdeadit': 'r/BrainsGoneWild'
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            
            # Check Post in DB
            post = Post.query.filter_by(title='Test Moan').first()
            self.assertIsNotNone(post)
            self.assertEqual(post.subdeadit, 'r/BrainsGoneWild')
            
            # Check Orchestrator was called
            mock_process.assert_called_once_with(post.id)

    @patch('backend.logic.generator.ZombieGenerator.generate_comment')
    def test_full_ai_orchestration(self, mock_generate):
        """
        Test that Orchestrator actually creates a comment when Generator returns data.
        """
        # Mock Generator output
        mock_generate.return_value = {
            "body": "Braaaains... good post...",
            "flair": "Hungry"
        }
        
        self.register_login()
        
        # We DON'T patch orchestrator here because we want to test its logic
        self.client.post('/create_post', data={
            'title': 'Orchestrator Test',
            'body': 'Checking if zombies appear.',
            'subdeadit': 'r/ZombieSurvival'
        }, follow_redirects=True)
        
        # Verify Post
        post = Post.query.filter_by(title='Orchestrator Test').first()
        self.assertIsNotNone(post)
        
        # Verify Zombie Logic (Orchestrator should have created a comment)
        comment = Comment.query.filter_by(post_id=post.id).first()
        self.assertIsNotNone(comment, "Orchestrator failed to create comment")
        self.assertEqual(comment.body, "Braaaains... good post...")
        self.assertTrue(comment.author.is_zombie)

if __name__ == '__main__':
    unittest.main()
