import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import TrendAnalyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trend_analyzer import TrendAnalyzer


class TestTrendAnalyzer(unittest.TestCase):
    """Test cases for the TrendAnalyzer class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.analyzer = TrendAnalyzer()
        
    @patch('trend_analyzer.openai.ChatCompletion.create')
    def test_analyze_trend(self, mock_openai):
        """Test the analyze_trend method with a mocked OpenAI response."""
        # Configure the mock to return a specific response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"score": 85, "reasoning": "Very popular meme with viral potential", "category": "Entertainment"}'
        mock_openai.return_value = mock_response
        
        # Call the method with test data
        result = self.analyzer.analyze_trend("Doge to the Moon")
        
        # Assert the results are as expected
        self.assertEqual(result['score'], 85)
        self.assertEqual(result['category'], "Entertainment")
        self.assertIn("viral potential", result['reasoning'])
        
    @patch('trend_analyzer.requests.get')
    def test_fetch_trends(self, mock_requests):
        """Test the fetch_trends method with mocked HTTP responses."""
        # Configure the mock to return a specific response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "trends": [
                {"name": "Crypto Boom", "volume": 25000},
                {"name": "AI Revolution", "volume": 18000}
            ]
        }
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        # Call the method
        trends = self.analyzer.fetch_trends(source="twitter")
        
        # Assert the results
        self.assertEqual(len(trends), 2)
        self.assertEqual(trends[0]["name"], "Crypto Boom")
        self.assertEqual(trends[1]["volume"], 18000)
        
    def test_calculate_virality_score(self):
        """Test the calculate_virality_score method with sample metrics."""
        # Test data
        metrics = {
            "mentions": 5000,
            "engagement_rate": 0.08,
            "growth_rate": 1.5,
            "sentiment_score": 0.7
        }
        
        # Call the method
        score = self.analyzer.calculate_virality_score(metrics)
        
        # Assert the score is within expected range
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        
        # Test with different data
        low_metrics = {
            "mentions": 100,
            "engagement_rate": 0.01,
            "growth_rate": 0.2,
            "sentiment_score": 0.3
        }
        low_score = self.analyzer.calculate_virality_score(low_metrics)
        
        # The higher metrics should produce a higher score
        self.assertGreater(score, low_score)
        

if __name__ == '__main__':
    unittest.main()

