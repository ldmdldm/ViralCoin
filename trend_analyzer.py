import os
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

class TrendAnalyzer:
    """
    Analyzes trending topics across various platforms and evaluates their potential
    for tokenization using AI.
    """
    
    def __init__(self):
        self.platforms = ["twitter", "reddit", "google", "tiktok"]
        self.min_score_threshold = 7.0  # Minimum score for a trend to be considered viable
        
    def fetch_trends(self, platform: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch trending topics from specified platform(s).
        
        Args:
            platform: Platform to fetch trends from ("twitter", "reddit", "google", "tiktok" or "all")
            limit: Maximum number of trends to fetch per platform
            
        Returns:
            List of trending topics with metadata
        """
        trends = []
        
        if platform == "all":
            platforms_to_fetch = self.platforms
        elif platform in self.platforms:
            platforms_to_fetch = [platform]
        else:
            raise ValueError(f"Invalid platform: {platform}. Available options: {', '.join(self.platforms)} or 'all'")
        
        # For demonstration purposes, using mockup data
        # In a real implementation, this would use platform-specific APIs
        for p in platforms_to_fetch:
            if p == "twitter":
                trends.extend(self._mock_twitter_trends(limit))
            elif p == "reddit":
                trends.extend(self._mock_reddit_trends(limit))
            elif p == "google":
                trends.extend(self._mock_google_trends(limit))
            elif p == "tiktok":
                trends.extend(self._mock_tiktok_trends(limit))
        
        # Add timestamp to each trend
        for trend in trends:
            trend["timestamp"] = datetime.now().isoformat()
            
        return trends
    
    def analyze_trend(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single trend using OpenAI API to determine its tokenization potential.
        
        Args:
            trend: Trend data including name, description, and platform
            
        Returns:
            Original trend data enhanced with AI analysis
        """
        # Create prompt for OpenAI
        prompt = self._create_analysis_prompt(trend)
        
        try:
            # Call OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert analyst of internet trends and crypto markets. Your task is to analyze trending topics and evaluate their potential as cryptocurrency tokens."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            
            # Extract and parse results
            analysis_text = response.choices[0].message.content
            analysis = json.loads(analysis_text)
            
            # Merge analysis with original trend data
            trend.update({
                "analysis": analysis,
                "tokenization_score": analysis.get("tokenization_score", 0),
                "market_potential": analysis.get("market_potential", "low"),
                "analysis_timestamp": datetime.now().isoformat()
            })
            
            return trend
            
        except Exception as e:
            print(f"Error analyzing trend {trend['name']}: {str(e)}")
            trend.update({
                "analysis_error": str(e),
                "tokenization_score": 0,
                "analysis_timestamp": datetime.now().isoformat()
            })
            return trend
            
    def batch_analyze_trends(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple trends and return enhanced data.
        
        Args:
            trends: List of trend data
            
        Returns:
            List of trends with AI analysis data
        """
        analyzed_trends = []
        
        for trend in trends:
            analyzed_trend = self.analyze_trend(trend)
            analyzed_trends.append(analyzed_trend)
            # Add a short delay to avoid rate limiting
            time.sleep(0.5)
        
        return analyzed_trends
        
    def get_top_trends_for_tokenization(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the top trends that have high potential for tokenization.
        
        Args:
            limit: Maximum number of top trends to return
            
        Returns:
            List of top trends sorted by tokenization potential
        """
        # Fetch trends from all platforms
        all_trends = self.fetch_trends(platform="all", limit=10)
        
        # Analyze all trends
        analyzed_trends = self.batch_analyze_trends(all_trends)
        
        # Filter trends that meet the minimum score threshold
        viable_trends = [
            trend for trend in analyzed_trends 
            if trend.get("tokenization_score", 0) >= self.min_score_threshold
        ]
        
        # Sort by tokenization score (descending)
        sorted_trends = sorted(
            viable_trends, 
            key=lambda x: x.get("tokenization_score", 0), 
            reverse=True
        )
        
        # Return top N trends
        return sorted_trends[:limit]
        
    def _create_analysis_prompt(self, trend: Dict[str, Any]) -> str:
        """
        Create a prompt for OpenAI analysis.
        
        Args:
            trend: Trend data
            
        Returns:
            Formatted prompt string
        """
        return f"""
        Please analyze this trending topic for its potential as a cryptocurrency token:
        
        Trend Name: {trend.get('name', 'Unknown')}
        Description: {trend.get('description', 'No description available')}
        Platform: {trend.get('platform', 'Unknown')}
        Volume: {trend.get('volume', 'Unknown')}
        Category: {trend.get('category', 'Unknown')}
        
        Please provide a comprehensive analysis in JSON format with the following structure:
        {{
            "summary": "Brief summary of the trend",
            "tokenization_score": A score from 1-10 indicating suitability for tokenization,
            "market_potential": "low", "medium", or "high",
            "target_demographic": "Description of potential investors",
            "meme_potential": A score from 1-10 indicating viral/meme potential,
            "risks": ["List of potential risks"],
            "token_utility_ideas": ["Possible utility for this token"],
            "marketing_angles": ["Potential marketing approaches"],
            "similar_successful_tokens": ["Examples of similar tokens if any"],
            "recommended_action": "create_token", "monitor", or "ignore"
        }}
        
        Ensure that the tokenization_score is objective and based on:
        - Virality and staying power of the trend
        - Cultural relevance and broad appeal
        - Potential for community formation
        - Uniqueness compared to existing tokens
        - Alignment with crypto culture and memes
        """
        
    # Mock data methods for demonstration
    def _mock_twitter_trends(self, limit: int) -> List[Dict[str, Any]]:
        trends = [
            {"name": "#AIRevolution", "description": "Discussions about the latest advancements in artificial intelligence", "platform": "twitter", "volume": 58200, "category": "technology"},
            {"name": "#DeFiSummer", "description": "Talk about upcoming DeFi projects and potential for a new boom", "platform": "twitter", "volume": 42100, "category": "finance"},
            {"name": "#SpaceExploration", "description": "Latest news and discussions about space missions and discoveries", "platform": "twitter", "volume": 38500, "category": "science"},
            {"name": "#MetaverseHomes", "description": "People sharing their virtual home designs in various metaverse platforms", "platform": "twitter", "volume": 29700, "category": "virtual reality"},
            {"name": "#QuantumComputing", "description": "Discussions about breakthroughs in quantum computing technology", "platform": "twitter", "volume": 24300, "category": "technology"}
        ]
        return trends[:limit]
        
    def _mock_reddit_trends(self, limit: int) -> List[Dict[str, Any]]:
        trends = [
            {"name": "Synthetic Biology", "description": "Discussions about creating artificial biological systems and organisms", "platform": "reddit", "volume": 45600, "category": "science"},
            {"name": "Decentralized Governance", "description": "Communities exploring new forms of governance using blockchain technology", "platform": "reddit", "volume": 38900, "category": "politics"},
            {"name": "Neural Link Interfaces", "description": "Advancements in brain-computer interfaces and neural technology", "platform": "reddit", "volume": 32800, "category": "technology"},
            {"name": "Climate Engineering", "description": "Discussions about technological solutions to climate change", "platform": "reddit", "volume": 29100, "category": "environment"},
            {"name": "Digital Nomad Hubs", "description": "Remote work communities forming in exotic locations around the world", "platform": "reddit", "volume": 26400, "category": "lifestyle"}
        ]
        return trends[:limit]
        
    def _mock_google_trends(self, limit: int) -> List[Dict[str, Any]]:
        trends = [
            {"name": "Web3 Gaming", "description": "Rising interest in blockchain-based gaming platforms", "platform": "google", "volume": 67500, "category": "gaming"},
            {"name": "Autonomous Drones", "description": "Consumer and commercial applications of autonomous drone technology", "platform": "google", "volume": 54300, "category": "technology"},
            {"name": "Tokenized Real Estate", "description": "Using blockchain to fractionalize real estate ownership", "platform": "google", "volume": 48900, "category": "real estate"},
            {"name": "Carbon Capture Tech", "description": "Technologies that remove carbon dioxide from the atmosphere", "platform": "google", "volume": 39200, "category": "environment"},
            {"name": "Fusion Energy Breakthrough", "description": "Recent advancements in fusion energy research", "platform": "google", "volume": 36700, "category": "energy"}
        ]
        return trends[:limit]
        
    def _mock_tiktok_trends(self, limit: int) -> List[Dict[str, Any]]:
        trends = [
            {"name": "#VirtualFashion", "description": "Digital clothing and fashion items for avatars and augmented reality", "platform": "tiktok", "volume": 78900, "category": "fashion"},
            {"name": "#AstralTravel", "description": "Videos about out-of-body experiences and astral projection techniques", "platform": "tiktok", "volume": 65400, "category": "spirituality"},
            {"name": "#CryptoArt", "description": "Artists sharing and selling their digital art as NFTs", "platform": "tiktok", "volume": 59200, "category": "art"},
            {"name": "#BioHacking", "description": "People experimenting with diet, exercise, and supplements to optimize biology", "platform": "tiktok", "volume": 52800, "category": "health"},
            {"name": "#SolarPunk", "description": "Aesthetics and lifestyle based on sustainable technology and positive future", "platform": "tiktok", "volume": 47600, "category": "culture"}
        ]
        return trends[:limit]


# Usage example
if __name__ == "__main__":
    analyzer = TrendAnalyzer()
    
    # Get top trends for tokenization
    top_trends = analyzer.get_top_trends_for_tokenization(limit=3)
    
    print(f"\nTop {len(top_trends)} Trends for Tokenization:")
    for i, trend in enumerate(top_trends, 1):
        print(f"\n{i}. {trend['name']} (Score: {trend['tokenization_score']}/10)")
        print(f"   Platform: {trend['platform']}")
        print(f"   Description: {trend['description']}")
        print(f"   Market Potential: {trend.get('market_potential', 'N/A')}")
        if 'analysis' in trend and 'recommended_action' in trend['analysis']:
            print(f"   Recommended Action: {trend['analysis']['recommended_action']}")

