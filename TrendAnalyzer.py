"""
TrendAnalyzer.py - Advanced Trend Analysis using OpenAI API

This module provides functionality to analyze trending topics using the OpenAI API
to generate insights and calculate trend scores for potential memecoins or utility tokens.

Features:
- Secure API key handling using environment variables
- OpenAI API integration for trend analysis
- Trend scoring algorithm based on AI analysis
- Token detail generation for trending topics

Usage:
    python TrendAnalyzer.py --update-scores
    
Dependencies:
    - openai
    - python-dotenv
"""

import os
import json
import time
import logging
import argparse
import datetime
from typing import List, Dict, Tuple, Any, Optional

# No need for requests as we're only using OpenAI API
from dotenv import load_dotenv
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trend_analyzer.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TrendAnalyzer")

# Load environment variables from .env file
load_dotenv()

class TrendAnalyzer:
    """
    Class for analyzing trends using the OpenAI API.
    
    This class provides methods to analyze trends using OpenAI's API
    and calculate trend scores for potential tokens.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TrendAnalyzer with OpenAI API configuration.
        
        Args:
            api_key: OpenAI API key (optional, will use env var if not provided)
        """
        # Load API key from environment if not provided
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass as parameter.")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        
        # Cache for API responses to reduce quota usage
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour in seconds
        
        logger.info("TrendAnalyzer initialized successfully")
    
    
    
    
    def get_top_trends(self, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Get top trends using OpenAI's API to generate potential trending topics.
        
        Args:
            limit: Maximum number of top trends to return
        
        Returns:
            List of tuples containing (trend_name, score)
        """
        try:
            # Use OpenAI to generate trending topics
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in cryptocurrency, blockchain, and internet culture trends."},
                    {"role": "user", "content": f"What are the top {limit*2} trending topics that could make good cryptocurrency themes today? For each trend, include a score from 0.1 to 1.0 indicating how viral or popular it might become. Provide the answer as a JSON list of objects with 'topic' and 'score' keys."}
                ],
                temperature=0.7,
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Extract the JSON part of the response
            import re
            import json
            
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    trends_data = json.loads(json_match.group(0))
                    # Convert to list of tuples, sort by score (descending) and limit
                    result = [(item["topic"], item["score"]) for item in trends_data]
                    result.sort(key=lambda x: x[1], reverse=True)
                    return result[:limit]
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from OpenAI response")
                    
            # Fallback: simple parsing
            trends = []
            for line in content.split("\n"):
                if ":" in line and any(char.isdigit() for char in line):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        topic = parts[0].strip().strip("\"'- .")
                        score_match = re.search(r'(\d+\.\d+|\d+)', parts[1])
                        if score_match:
                            score = float(score_match.group(0))
                            if 0 <= score <= 1:
                                trends.append((topic, score))
            
            # Sort and limit results
            trends.sort(key=lambda x: x[1], reverse=True)
            return trends[:limit]
            
        except Exception as e:
            logger.exception(f"Error getting top trends from OpenAI: {e}")
            return []
    
    def analyze_trend_with_ai(self, trend_name: str) -> Dict[str, Any]:
        """
        Analyze a trend using OpenAI's API to get insights.
        
        Args:
            trend_name: The name of the trend to analyze
            
        Returns:
            Dictionary containing AI analysis results
        """
        try:
            # Create a descriptive prompt for the AI
            prompt = f"""
            Analyze the following trend topic: "{trend_name}"
            
            Please provide the following information:
            1. Brief description of what this trend is about
            2. Classification: Is it related to meme culture, technology, finance, or other categories?
            3. Potential as a memecoin theme vs utility token theme (score from 1-10 for each)
            4. Projected longevity (short-term, medium-term, long-term)
            5. Key associated keywords and hashtags
            
            Format the response as a structured JSON object.
            """
            # Call the OpenAI API to analyze the trend
            # Check cache first
            cache_key = f"trend_analysis_{trend_name}"
            if cache_key in self.cache and time.time() - self.cache[cache_key]["timestamp"] < self.cache_expiry:
                logger.info(f"Using cached analysis for trend: {trend_name}")
                return self.cache[cache_key]["data"]

            try:
                # Make the API call to OpenAI
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert in trend analysis, cryptocurrency markets, and blockchain technology."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                )
                
                # Extract the content from the response
                content = response.choices[0].message.content
                
                # Try to parse the JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                
                if json_match:
                    try:
                        result = json.loads(json_match.group(0))
                        # Cache the result
                        self.cache[cache_key] = {
                            "timestamp": time.time(),
                            "data": result
                        }
                        return result
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON from OpenAI response for trend: {trend_name}")
                
                # Fallback: Return a structured response based on the content
                result = {
                    "trend_name": trend_name,
                    "description": "Analysis not available in structured format",
                    "raw_analysis": content,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Cache the result
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": result
                }
                return result
                
            except Exception as e:
                logger.exception(f"Error analyzing trend with AI: {e}")
                return {
                    "trend_name": trend_name,
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                }
        except Exception as e:
            logger.exception(f"Error in analyzing trend: {e}")
            return {
                "trend_name": trend_name,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
