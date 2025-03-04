import random
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class TrendAnalyzer:
    """
    Analyzes trending topics from various social media platforms and generates
    token configurations based on trend analysis.
    """
    
    def __init__(self, cache_timeout: int = 300):
        """
        Initialize the TrendAnalyzer.
        
        Args:
            cache_timeout (int): Time in seconds to cache trend results (default: 300)
        """
        self.cache_timeout = cache_timeout
        self.cache = {}
        self.last_fetch_time = 0
        self.memecoin_keywords = [
            "doge", "shib", "moon", "pepe", "wojak", "chad", "ape", "meme",
            "cat", "dog", "elon", "rocket", "diamond", "hands", "fomo", "hodl"
        ]
        
    def get_top_trends(self, limit: int = 3) -> List[Dict]:
        """
        Get top trending topics from Twitter, Reddit, and Google.
        
        Args:
            limit (int): Maximum number of trends to return
            
        Returns:
            List of trend dictionaries with name and score
        """
        current_time = time.time()
        
        # Check cache validity
        if current_time - self.last_fetch_time < self.cache_timeout and self.cache:
            return self.cache[:limit]
        
        # Fetch trends from all sources
        twitter_trends = self._fetch_twitter_trends()
        reddit_trends = self._fetch_reddit_trends()
        google_trends = self._fetch_google_trends()
        
        # Combine and normalize scores
        all_trends = {}
        
        # Process Twitter trends (weight: 0.4)
        for trend, score in twitter_trends:
            if trend in all_trends:
                all_trends[trend] += score * 0.4
            else:
                all_trends[trend] = score * 0.4
        
        # Process Reddit trends (weight: 0.35)
        for trend, score in reddit_trends:
            if trend in all_trends:
                all_trends[trend] += score * 0.35
            else:
                all_trends[trend] = score * 0.35
        
        # Process Google trends (weight: 0.25)
        for trend, score in google_trends:
            if trend in all_trends:
                all_trends[trend] += score * 0.25
            else:
                all_trends[trend] = score * 0.25
        
        # Convert to list and sort by score
        result = [{"name": name, "score": round(score, 2)} for name, score in all_trends.items()]
        result.sort(key=lambda x: x["score"], reverse=True)
        
        # Update cache
        self.cache = result
        self.last_fetch_time = current_time
        
        return result[:limit]
    
    def generate_token_details(self, trend_name: str, trend_score: float) -> Dict:
        """
        Generate token details for a trend.
        
        Args:
            trend_name (str): Name of the trend
            trend_score (float): Score of the trend
            
        Returns:
            Dictionary with token details
        """
        trend_type = self._classify_trend_type(trend_name)
        
        # Base token details
        token_details = {
            "name": f"{trend_name.title()} Token",
            "symbol": self._generate_symbol(trend_name),
            "description": f"Token based on the trending topic: {trend_name}",
            "created_at": datetime.now().isoformat(),
            "trend_score": trend_score,
            "trend_type": trend_type,
            "initial_supply": self._calculate_initial_supply(trend_score)
        }
        
        # Add type-specific details
        if trend_type == "memecoin":
            token_details.update({
                "burn_rate": min(int(trend_score * 15), 300),  # Max 3% burn rate
                "max_supply": token_details["initial_supply"] * 10,
                "is_mintable": False,
                "meme_power": int(trend_score * 10)
            })
        else:  # utility token
            token_details.update({
                "burn_rate": min(int(trend_score * 5), 100),  # Max 1% burn rate
                "max_supply": token_details["initial_supply"] * 4,
                "is_mintable": True,
                "utility_score": int(trend_score * 10)
            })
        
        return token_details
    
    def _classify_trend_type(self, trend: str) -> str:
        """
        Classify a trend as either a memecoin or a utility token.
        
        Args:
            trend (str): Trend name to classify
            
        Returns:
            String indicating the trend type: "memecoin" or "utility"
        """
        # Check if any memecoin keywords are in the trend
        trend_lower = trend.lower()
        
        for keyword in self.memecoin_keywords:
            if keyword in trend_lower:
                return "memecoin"
        
        # For this demo, we'll use a simple rule:
        # If the trend name is shorter than 5 characters, classify as memecoin
        # If the first letter of the trend is in the first half of the alphabet (a-m), classify as memecoin
        if len(trend) < 5 or trend[0].lower() in "abcdefghijklm":
            return "memecoin"
        
        return "utility"
    
    def _fetch_twitter_trends(self) -> List[Tuple[str, float]]:
        """
        Fetch trends from Twitter.
        
        Returns:
            List of (trend_name, score) tuples
        """
        # Mock Twitter trends
        twitter_trends = [
            ("NFT", 9.7),
            ("Bitcoin", 9.5),
            ("Ethereum", 9.2),
            ("GameFi", 8.8),
            ("Web3", 8.5),
            ("AI", 8.3),
            ("DeFi", 8.0),
            ("Metaverse", 7.8),
            ("DAO", 7.5),
            ("Blockchain", 7.3)
        ]
        
        # Add some randomness to scores
        randomized_trends = []
        for trend, score in twitter_trends:
            # Add random variation ±0.5
            adjusted_score = min(10.0, max(1.0, score + (random.random() - 0.5)))
            randomized_trends.append((trend, adjusted_score))
        
        return randomized_trends
    
    def _fetch_reddit_trends(self) -> List[Tuple[str, float]]:
        """
        Fetch trends from Reddit.
        
        Returns:
            List of (trend_name, score) tuples
        """
        # Mock Reddit trends
        reddit_trends = [
            ("Solana", 9.6),
            ("Polygon", 9.3),
            ("Cardano", 9.0),
            ("zkSync", 8.7),
            ("PEPE", 8.4),
            ("Airdrop", 8.2),
            ("Staking", 7.9),
            ("SHIB", 7.7),
            ("Arbitrum", 7.4),
            ("Optimism", 7.2)
        ]
        
        # Add some randomness to scores
        randomized_trends = []
        for trend, score in reddit_trends:
            # Add random variation ±0.5
            adjusted_score = min(10.0, max(1.0, score + (random.random() - 0.5)))
            randomized_trends.append((trend, adjusted_score))
        
        return randomized_trends
        
    def _fetch_google_trends(self) -> List[Tuple[str, float]]:
        """
        Fetch trends from Google.
        
        Returns:
            List of (trend_name, score) tuples
        """
        # Mock Google trends
        google_trends = [
            ("Crypto", 9.8),
            ("Binance", 9.4),
            ("Coinbase", 9.1),
            ("Dogecoin", 8.9),
            ("Wallet", 8.6),
            ("Trading", 8.1),
            ("Mining", 7.6),
            ("Layer2", 7.5),
            ("Token", 7.3),
            ("Yield", 7.1)
        ]
        
        # Add some randomness to scores
        randomized_trends = []
        for trend, score in google_trends:
            # Add random variation ±0.5
            adjusted_score = min(10.0, max(1.0, score + (random.random() - 0.5)))
            randomized_trends.append((trend, adjusted_score))
        
        return randomized_trends
    
    def _calculate_initial_supply(self, trend_score: float) -> int:
        """
        Calculate initial token supply based on trend score.
        
        Args:
            trend_score (float): Score of the trend
            
        Returns:
            Initial token supply
        """
        # Higher trend score = higher initial supply
        base_supply = 1_000_000  # 1 million base supply
        score_multiplier = trend_score / 5  # Range: 0-2 for scores 0-10
        
        return int(base_supply * score_multiplier)
    
    def _generate_symbol(self, trend_name: str) -> str:
        """
        Generate a token symbol from the trend name.
        
        Args:
            trend_name (str): Name of the trend
            
        Returns:
            Token symbol (3-5 characters)
        """
        # Simple approach: take first 3-4 letters and uppercase
        words = trend_name.split()
        
        if len(words) > 1:
            # For multi-word trends, take first letter of each word
            symbol = ''.join(word[0] for word in words if word)
            if len(symbol) < 3:
                # Add more letters from the first word if needed
                symbol += words[0][1:4-len(symbol)]
        else:
            # For single-word trends, take first 3-4 letters
            symbol = trend_name[:min(4, len(trend_name))]
        
        return symbol.upper()

