"""
Tests for the TrendAnalyzer class.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.trend_analyzer import TrendAnalyzer

class TestTrendAnalyzer(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TrendAnalyzer()
    
    @patch('ai.trend_analyzer.TrendAnalyzer._fetch_twitter_trends')
    @patch('ai.trend_analyzer.TrendAnalyzer._fetch_reddit_trends')
    @patch('ai.trend_analyzer.TrendAnalyzer._fetch_google_trends')
    def test_get_top_trends(self, mock_google, mock_reddit, mock_twitter):
        """Test the get_top_trends method."""
        # Mock the API responses
        mock_twitter.return_value = [
            {"topic": "Python", "score": 0.8},
            {"topic": "Blockchain", "score": 0.7}
        ]
        mock_reddit.return_value = [
            {"topic": "Python", "score": 0.9},
            {"topic": "NFT", "score": 0.6}
        ]
        mock_google.return_value = [
            {"topic": "Cryptocurrency", "score": 0.75},
            {"topic": "Python", "score": 0.65}
        ]
        
        top_trends = self.analyzer.get_top_trends(limit=3)
        
        # Assertions
        self.assertEqual(len(top_trends), 3)
        # Python should be the top trend since it appears in all sources
        self.assertEqual(top_trends[0][0], "Python")
        self.assertTrue(top_trends[0][1] > 0.7)  # Score should be high
    
    def test_generate_token_details(self):
        """Test the generate_token_details method."""
        # Test with a memecoin-style trend
        trend_name = "DogeAI"
        trend_score = 0.95
        
        token_details = self.analyzer.generate_token_details(trend_name, trend_score)
        
        # Basic assertions
        self.assertIn('name', token_details)
        self.assertIn('symbol', token_details)
        self.assertIn('initial_supply', token_details)
        self.assertIn('tokenomics_type', token_details)
        
        # The name should contain the trend name
        self.assertIn(trend_name, token_details['name'])
        
        # The initial supply should be a positive number
        self.assertGreater(token_details['initial_supply'], 0)
    
    def test_classify_trend_type(self):
        """Test the trend type classification."""
        # These should be classified as different types
        memecoin_trend = "Doge Moon"
        utility_trend = "Smart Contract Platform"
        
        # Using the protected method for testing
        memecoin_type = self.analyzer._classify_trend_type(memecoin_trend)
        utility_type = self.analyzer._classify_trend_type(utility_trend)
        
        # They should be classified differently
        self.assertNotEqual(memecoin_type, utility_type)

if __name__ == '__main__':
    unittest.main()

